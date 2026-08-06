from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from diskcleaner.gui.components.bottom_action_button import BottomActionButton
from diskcleaner.gui.components.duplicate_group import DuplicateGroupBox
from diskcleaner.gui.typo import headline_small

BUTTON_TEXT_DEFAULT = "그룹당 1개 남기고 삭제"
BUTTON_TEXT_SELECTED = "선택 삭제"


class DuplicatePage(QWidget):
    delete_requested = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("duplicatePage")

        self._groups: list[DuplicateGroupBox] = []
        self._group_files: list[list[dict]] = []
        self._is_dark = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

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
        self.list_layout.setSpacing(16)
        self.list_layout.addStretch()

        self.scroll_area.setWidget(self.list_container)
        layout.addWidget(self.scroll_area, stretch=1)

        self.action_button = BottomActionButton()
        self.action_button.set_text(BUTTON_TEXT_DEFAULT)
        self.action_button.clicked.connect(self._on_action_clicked)
        layout.addWidget(self.action_button, alignment=Qt.AlignHCenter)

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

    def update_responsive_size(self, container_width: int):
        for group_box in self._groups:
            group_box.update_responsive_size(container_width)
        self.action_button.update_responsive_size(container_width)

    def refresh_fonts(self):
        self.title_label.setFont(headline_small())

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
