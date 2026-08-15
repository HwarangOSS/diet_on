from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from diskcleaner.gui.components.bottom_action_button import BottomActionButton
from diskcleaner.gui.components.duplicate_group import DuplicateGroupBox
from diskcleaner.gui.components.side_action_button import SideActionButton
from diskcleaner.gui.typo import FontFamily, get_font

from . import styles

BUTTON_TEXT_DEFAULT = "그룹당 1개 남기고 삭제"
BUTTON_TEXT_SELECTED = "선택 삭제"

BACK_BUTTON_TEXT = "Back"


def _design_scale(container_width: int) -> float:
    return container_width / styles.REFERENCE_WIDTH


def _title_font(scale: float):
    return get_font(FontFamily.PLAY_REGULAR, 22, role="headline_small", scale=scale)


class DuplicatePage(QWidget):
    delete_requested = Signal(list)
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("duplicatePage")

        self._groups: list[DuplicateGroupBox] = []
        self._group_files: list[list[dict]] = []
        self._is_dark = False

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.back_button = SideActionButton()
        self.back_button.set_text(BACK_BUTTON_TEXT)
        self.back_button.clicked.connect(self.back_requested.emit)
        outer.addWidget(self.back_button, alignment=Qt.AlignVCenter)

        self._layout = layout = QVBoxLayout()
        outer.addLayout(layout, stretch=1)
        self._right_spacer = QWidget()
        outer.addWidget(self._right_spacer)

        self.title_label = QLabel("Duplicate")
        self.title_label.setObjectName("detailTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        layout.addSpacing(0)
        self._title_gap = layout.itemAt(layout.count() - 1).spacerItem()

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("detailScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

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

        self.update_responsive_size(styles.REFERENCE_WIDTH)

    # API
    def set_groups(self, groups: list[dict]):
        for group_box in self._groups:
            self.list_layout.removeWidget(group_box)
            group_box.setParent(None)
            group_box.deleteLater()
        self._groups.clear()
        self._group_files = [g["files"] for g in groups]

        insert_at = self.list_layout.count() - 1
        for g in groups:
            group_box = DuplicateGroupBox()
            group_box.set_dark(self._is_dark)
            group_box.set_group(g["name"], g["files"])
            group_box.file_toggled.connect(self._on_item_toggled)
            self.list_layout.insertWidget(insert_at, group_box)
            insert_at += 1
            self._groups.append(group_box)

        self.update_responsive_size(self.width() or styles.REFERENCE_WIDTH)
        self._refresh_button_text()

    def apply_theme(self, dark: bool):
        self._is_dark = dark
        for group_box in self._groups:
            group_box.set_dark(dark)
        self.action_button.set_dark(dark)
        self.back_button.set_dark(dark)

    def update_responsive_size(self, container_width: int):
        scale = _design_scale(container_width)

        self.title_label.setFont(_title_font(scale))

        margin = round(styles.REF_MARGIN * scale)
        margin_top = round(styles.REF_MARGIN_TOP * scale)
        margin_bottom = round(styles.REF_MARGIN_BOTTOM * scale)
        self._layout.setContentsMargins(margin, margin_top, margin, margin_bottom)
        self._layout.setSpacing(round(styles.REF_PAGE_GAP * scale))
        self._title_gap.changeSize(
            0, round(styles.REF_TITLE_GAP * scale), QSizePolicy.Minimum, QSizePolicy.Fixed
        )
        self._layout.invalidate()
        self.list_layout.setSpacing(round(styles.REF_LIST_GAP * scale))
        back_button_width = self.back_button.width()
        content_width = max(1, container_width - back_button_width - 2 * margin)
        self._right_spacer.setFixedWidth(back_button_width)

        for group_box in self._groups:
            group_box.update_responsive_size(content_width)
        self.action_button.update_responsive_size(
            round(content_width * styles.ACTION_BUTTON_WIDTH_SCALE),
            scale=scale,
            height_scale=styles.ACTION_BUTTON_HEIGHT_SCALE,
            text_size=styles.ACTION_BUTTON_TEXT_SIZE,
        )
        self.back_button.update_responsive_size(self.height(), scale=scale)

    def refresh_fonts(self):
        self.update_responsive_size(self.width() or styles.REFERENCE_WIDTH)
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
