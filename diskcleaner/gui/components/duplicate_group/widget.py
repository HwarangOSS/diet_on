from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from diskcleaner.gui.components.file_list_item import FileListItem
from diskcleaner.gui.theme import LIGHT
from diskcleaner.gui.typo import body_md, group, rem

from . import styles


class DuplicateGroupBox(QWidget):
    file_toggled = Signal(int, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("duplicateGroupBox")
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._is_dark = False
        self._items: list[FileListItem] = []

        outer = QVBoxLayout(self)
        padding = rem(styles.PADDING_REM)
        outer.setContentsMargins(padding, padding, padding, padding)
        outer.setSpacing(rem(styles.HEADER_GAP_REM))

        header_row = QHBoxLayout()
        header_row.setSpacing(4)

        self.group_name_label = QLabel()
        self.group_name_label.setObjectName("duplicateGroupName")
        self.group_name_label.setFont(group())
        header_row.addWidget(self.group_name_label)

        self.group_count_label = QLabel()
        self.group_count_label.setObjectName("duplicateGroupCount")
        self.group_count_label.setFont(body_md())
        header_row.addWidget(self.group_count_label)
        header_row.addStretch()

        outer.addLayout(header_row)

        self.items_layout = QVBoxLayout()
        self.items_layout.setSpacing(rem(styles.ITEM_GAP_REM))
        outer.addLayout(self.items_layout)

        self._refresh_style()

    # API
    def set_group(self, group_name: str, files: list[dict]):
        """
        files: [{"name": str, "path": str, "size_bytes": int}, ...]
        files[0]이 최상위(원본 추정) 파일 - 기본 비선택, 나머지는 기본 선택.
        """
        for item in self._items:
            self.items_layout.removeWidget(item)
            item.setParent(None)
            item.deleteLater()
        self._items.clear()

        self.group_name_label.setText(group_name)
        self.group_count_label.setText(f"· {len(files)}개 파일 동일")

        for i, f in enumerate(files):
            item = FileListItem()
            item.set_file(f["name"], f["path"], f["size_bytes"])
            item.set_dark(self._is_dark)
            item.set_selected(i != 0)
            item.toggled.connect(lambda selected, idx=i: self.file_toggled.emit(idx, selected))
            self.items_layout.addWidget(item)
            self._items.append(item)

    def selected_states(self) -> list[bool]:
        return [item.is_selected() for item in self._items]

    def item_count(self) -> int:
        return len(self._items)

    def set_dark(self, dark: bool):
        self._is_dark = dark
        self._refresh_style()
        for item in self._items:
            item.set_dark(dark)

    def refresh_fonts(self):
        self.group_name_label.setFont(group())
        self.group_count_label.setFont(body_md())
        for item in self._items:
            item.refresh_fonts()

    def update_responsive_size(self, container_width: int):
        padding = rem(styles.PADDING_REM)
        self.layout().setContentsMargins(padding, padding, padding, padding)
        self.layout().setSpacing(rem(styles.HEADER_GAP_REM))
        self.items_layout.setSpacing(rem(styles.ITEM_GAP_REM))
        self._refresh_style()

        for item in self._items:
            item.update_responsive_size(container_width)

    # 내부
    def _refresh_style(self):
        bg = styles.DARK_BG if self._is_dark else styles.LIGHT_BG
        text_color = "#FFFFFF" if self._is_dark else LIGHT.text_primary

        self.setStyleSheet(
            f"QWidget#duplicateGroupBox {{"
            f" background: {bg};"
            f" border-radius: {rem(styles.CORNER_RADIUS_REM)}px;"
            f" }}"
            f"QLabel#duplicateGroupName, QLabel#duplicateGroupCount {{"
            f" color: {text_color}; background: transparent;"
            f" }}"
        )
