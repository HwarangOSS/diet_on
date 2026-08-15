from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from diskcleaner.gui.components.bottom_action_button import BottomActionButton
from diskcleaner.gui.components.duplicate_group import DuplicateGroupBox
from diskcleaner.gui.typo import body_mini, headline_small, rem

BUTTON_TEXT_DEFAULT = "그룹당 1개 남기고 삭제"
BUTTON_TEXT_SELECTED = "선택 삭제"

# rem 단위(1rem=16px)
PAGE_MARGIN_REM = 20 / 16
PAGE_GAP_REM = 16 / 16
LIST_GAP_REM = 16 / 16


class DuplicatePage(QWidget):
    """중복 파일 상세 화면 - 그룹별로 원본 제외 사본을 기본 선택해 보여줌."""

    delete_requested = Signal(list)
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("duplicatePage")

        self._groups: list[DuplicateGroupBox] = []
        self._group_files: list[list[dict]] = []
        self._is_dark = False

        self._layout = layout = QVBoxLayout(self)

        self.back_label = QLabel("‹ 뒤로")
        self.back_label.setObjectName("detailBackLabel")
        self.back_label.setFont(body_mini())
        self.back_label.setCursor(Qt.PointingHandCursor)
        self.back_label.mousePressEvent = lambda _event: self.back_requested.emit()
        layout.addWidget(self.back_label, alignment=Qt.AlignLeft)

        self.title_label = QLabel("Duplicate")
        self.title_label.setObjectName("detailTitle")
        self.title_label.setFont(headline_small())
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("detailScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.list_container = QWidget()
        self.list_container.setObjectName("duplicateListContainer")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.addStretch()

        self.scroll_area.setWidget(self.list_container)
        layout.addWidget(self.scroll_area, stretch=1)

        self.action_button = BottomActionButton()
        self.action_button.set_text(BUTTON_TEXT_DEFAULT)
        self.action_button.clicked.connect(self._on_action_clicked)
        layout.addWidget(self.action_button, alignment=Qt.AlignHCenter)

        self._apply_responsive_size()

    # API
    def set_groups(self, groups: list[dict]):
        for group_box in self._groups:
            self.list_layout.removeWidget(group_box)
            group_box.setParent(None)
            group_box.deleteLater()
        self._groups.clear()
        self._group_files = [g["files"] for g in groups]

        for g in groups:
            group_box = DuplicateGroupBox()
            group_box.set_dark(self._is_dark)
            group_box.set_group(g["name"], g["files"])
            group_box.file_toggled.connect(self._on_item_toggled)
            self.list_layout.insertWidget(self.list_layout.count() - 1, group_box)
            self._groups.append(group_box)

        self._refresh_button_text()

    def apply_theme(self, dark: bool):
        self._is_dark = dark
        for group_box in self._groups:
            group_box.set_dark(dark)
        self.action_button.set_dark(dark)

    def _apply_responsive_size(self):
        margin = rem(PAGE_MARGIN_REM)
        self._layout.setContentsMargins(margin, margin, margin, margin)
        self._layout.setSpacing(rem(PAGE_GAP_REM))
        self.list_layout.setSpacing(rem(LIST_GAP_REM))

    def update_responsive_size(self, container_width: int):
        self._apply_responsive_size()

        for group_box in self._groups:
            group_box.update_responsive_size(container_width)
        self.action_button.update_responsive_size(container_width)

    def refresh_fonts(self):
        self.back_label.setFont(body_mini())
        self.title_label.setFont(headline_small())
        for group_box in self._groups:
            group_box.refresh_fonts()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_responsive_size(self.width())

    # 내부
    def _on_item_toggled(self, _index: int, _selected: bool):
        self._refresh_button_text()

    def _is_default_selection(self) -> bool:
        for group_box in self._groups:
            states = group_box.selected_states()
            if not states:
                continue
            if states[0] or not all(states[1:]):
                return False
        return True

    def _refresh_button_text(self):
        text = BUTTON_TEXT_DEFAULT if self._is_default_selection() else BUTTON_TEXT_SELECTED
        self.action_button.set_text(text)

    def _on_action_clicked(self):
        selected_paths = []
        for files, group_box in zip(self._group_files, self._groups):
            for f, selected in zip(files, group_box.selected_states()):
                if selected:
                    selected_paths.append(f["path"])
        self.delete_requested.emit(selected_paths)
