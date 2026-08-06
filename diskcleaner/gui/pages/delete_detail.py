from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from diskcleaner.gui.components.bottom_action_button import BottomActionButton
from diskcleaner.gui.components.file_list_item import FileListItem
from diskcleaner.gui.typo import headline_small

BUTTON_TEXT_DEFAULT = "전체 삭제"
BUTTON_TEXT_SELECTED = "선택 삭제"


class DeletePage(QWidget):
    delete_requested = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("deletePage")

        self._items: list[FileListItem] = []
        self._files: list[dict] = []
        self._is_dark = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        self.title_label = QLabel("Delete")
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
        self.list_container.setObjectName("deleteListContainer")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(12)
        self.list_layout.addStretch()

        self.scroll_area.setWidget(self.list_container)
        layout.addWidget(self.scroll_area, stretch=1)

        self.action_button = BottomActionButton()
        self.action_button.set_text(BUTTON_TEXT_DEFAULT)
        self.action_button.clicked.connect(self._on_action_clicked)
        layout.addWidget(self.action_button, alignment=Qt.AlignHCenter)

    # API
    def set_files(self, files: list[dict]):
        for item in self._items:
            self.list_layout.removeWidget(item)
            item.setParent(None)
            item.deleteLater()
        self._items.clear()
        self._files = files

        for f in files:
            item = FileListItem()
            item.set_file(f["name"], f["path"], f["size_bytes"], f.get("hashtags"))
            item.set_dark(self._is_dark)
            item.toggled.connect(self._on_item_toggled)
            self.list_layout.insertWidget(self.list_layout.count() - 1, item)
            self._items.append(item)

        self._refresh_button_text()

    def apply_theme(self, dark: bool):
        self._is_dark = dark
        for item in self._items:
            item.set_dark(dark)
        self.action_button.set_dark(dark)

    def update_responsive_size(self, container_width: int):
        for item in self._items:
            item.update_responsive_size(container_width)
        self.action_button.update_responsive_size(container_width)

    def refresh_fonts(self):
        self.title_label.setFont(headline_small())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_responsive_size(self.width())

    # 내부
    def _on_item_toggled(self, _selected: bool):
        self._refresh_button_text()

    def _refresh_button_text(self):
        all_selected = all(item.is_selected() for item in self._items)
        self.action_button.set_text(BUTTON_TEXT_DEFAULT if all_selected else BUTTON_TEXT_SELECTED)

    def _on_action_clicked(self):
        selected_paths = [
            f["path"] for f, item in zip(self._files, self._items) if item.is_selected()
        ]
        self.delete_requested.emit(selected_paths)
