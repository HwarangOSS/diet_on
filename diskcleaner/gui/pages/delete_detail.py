from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from diskcleaner.gui.components.bottom_action_button import BottomActionButton
from diskcleaner.gui.components.file_list_item import FileListItem
from diskcleaner.gui.result_mapping import REVIEW_CATEGORY_LABEL, SAFE_CATEGORY_LABEL
from diskcleaner.gui.typo import body_mini, headline_small, rem, set_global_scale

BUTTON_TEXT_DEFAULT = "전체 삭제"
BUTTON_TEXT_SELECTED = "선택 삭제"

CHEVRON_EXPANDED = "▼"
CHEVRON_COLLAPSED = "▶"

# rem 단위(1rem=16px)
PAGE_MARGIN_REM = 20 / 16
PAGE_GAP_REM = 16 / 16
LIST_GAP_REM = 12 / 16
HEADER_MARGIN_H_REM = 4 / 16


class DeletePage(QWidget):
    """삭제 후보 상세 화면 - 카테고리별로 묶어서 보여주고 그룹/개별 선택 지원."""

    delete_requested = Signal(list)
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("deletePage")

        self._items: list[FileListItem] = []
        self._files: list[dict] = []
        self._group_headers: list[QWidget] = []
        self._group_sections: dict[str, dict] = {}
        self._is_dark = False

        self._layout = layout = QVBoxLayout(self)

        self.back_label = QLabel("‹ 뒤로")
        self.back_label.setObjectName("detailBackLabel")
        self.back_label.setFont(body_mini())
        self.back_label.setCursor(Qt.PointingHandCursor)
        self.back_label.mousePressEvent = lambda _event: self.back_requested.emit()
        layout.addWidget(self.back_label, alignment=Qt.AlignLeft)

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
        self.list_layout.addStretch()

        self.scroll_area.setWidget(self.list_container)
        layout.addWidget(self.scroll_area, stretch=1)

        self.action_button = BottomActionButton()
        self.action_button.set_text(BUTTON_TEXT_DEFAULT)
        self.action_button.clicked.connect(self._on_action_clicked)
        layout.addWidget(self.action_button, alignment=Qt.AlignHCenter)

        self._apply_responsive_size()

    # API
    def set_files(self, files: list[dict]):
        for item in self._items:
            self.list_layout.removeWidget(item)
            item.setParent(None)
            item.deleteLater()
        self._items.clear()
        for header in self._group_headers:
            self.list_layout.removeWidget(header)
            header.setParent(None)
            header.deleteLater()
        self._group_headers.clear()
        self._group_sections.clear()
        self._files = []

        groups: dict[str, list[dict]] = {}
        for f in files:
            groups.setdefault(f.get("category") or SAFE_CATEGORY_LABEL, []).append(f)

        insert_at = self.list_layout.count() - 1  # 맨 끝 stretch 앞에 계속 끼워넣음
        for category, group_files in groups.items():
            header, title_label, checkbox = self._make_group_header(category, len(group_files))
            self.list_layout.insertWidget(insert_at, header)
            insert_at += 1
            self._group_headers.append(header)

            group_items: list[FileListItem] = []
            for f in group_files:
                item = FileListItem()
                item.set_file(
                    f["name"], f["path"], f["size_bytes"], f.get("hashtags"), f.get("reason")
                )
                if category == REVIEW_CATEGORY_LABEL:
                    item.set_selected(False, emit=False)
                item.set_dark(self._is_dark)
                item.toggled.connect(self._on_item_toggled)
                self.list_layout.insertWidget(insert_at, item)
                insert_at += 1
                self._items.append(item)
                group_items.append(item)
                self._files.append(f)

            self._group_sections[category] = {
                "items": group_items,
                "title_label": title_label,
                "checkbox": checkbox,
                "base_text": f"{category} ({len(group_files)})",
                "collapsed": False,
            }
            checkbox.clicked.connect(lambda _checked, items=group_items: self._toggle_group(items))
            header.mousePressEvent = lambda _event, cat=category: self._toggle_collapse(cat)

        self._refresh_button_text()
        self._refresh_group_checkboxes()

    def apply_theme(self, dark: bool):
        self._is_dark = dark
        for item in self._items:
            item.set_dark(dark)
        self.action_button.set_dark(dark)

    def _apply_responsive_size(self):
        margin = rem(PAGE_MARGIN_REM)
        self._layout.setContentsMargins(margin, margin, margin, margin)
        self._layout.setSpacing(rem(PAGE_GAP_REM))
        self.list_layout.setSpacing(rem(LIST_GAP_REM))

        header_margin = rem(HEADER_MARGIN_H_REM)
        for header in self._group_headers:
            header.layout().setContentsMargins(header_margin, 0, header_margin, 0)

    def update_responsive_size(self, container_width: int):
        set_global_scale(container_width)
        self._apply_responsive_size()

        for item in self._items:
            item.update_responsive_size(container_width)
        self.action_button.update_responsive_size(container_width)

    def refresh_fonts(self):
        self.back_label.setFont(body_mini())
        self.title_label.setFont(headline_small())
        for section in self._group_sections.values():
            section["title_label"].setFont(body_mini())
            section["checkbox"].setFont(body_mini())
        for item in self._items:
            item.refresh_fonts()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_responsive_size(self.width())

    # 내부
    def _make_group_header(self, category: str, count: int) -> tuple[QWidget, QLabel, QCheckBox]:
        header = QWidget()
        header.setObjectName("deleteGroupHeader")
        header.setCursor(Qt.PointingHandCursor)
        row = QHBoxLayout(header)
        header_margin = rem(HEADER_MARGIN_H_REM)
        row.setContentsMargins(header_margin, 0, header_margin, 0)

        title = QLabel(f"{CHEVRON_EXPANDED} {category} ({count})")
        title.setObjectName("deleteGroupTitle")
        title.setFont(body_mini())
        row.addWidget(title)
        row.addStretch()

        checkbox = QCheckBox("전체 선택")
        checkbox.setObjectName("deleteGroupCheckbox")
        checkbox.setFont(body_mini())
        checkbox.setTristate(True)
        checkbox.setCursor(Qt.PointingHandCursor)
        row.addWidget(checkbox)

        return header, title, checkbox

    def _toggle_group(self, items: list[FileListItem]):
        select_all = not all(item.is_selected() for item in items)
        for item in items:
            item.set_selected(select_all, emit=False)
        self._refresh_button_text()
        self._refresh_group_checkboxes()

    def _refresh_group_checkboxes(self):
        for section in self._group_sections.values():
            states = [item.is_selected() for item in section["items"]]
            checkbox = section["checkbox"]
            checkbox.blockSignals(True)
            if all(states):
                checkbox.setCheckState(Qt.Checked)
            elif not any(states):
                checkbox.setCheckState(Qt.Unchecked)
            else:
                checkbox.setCheckState(Qt.PartiallyChecked)
            checkbox.blockSignals(False)

    def _toggle_collapse(self, category: str):
        section = self._group_sections[category]
        collapsed = not section["collapsed"]
        section["collapsed"] = collapsed
        for item in section["items"]:
            item.setVisible(not collapsed)
        chevron = CHEVRON_COLLAPSED if collapsed else CHEVRON_EXPANDED
        section["title_label"].setText(f"{chevron} {section['base_text']}")

    def _on_item_toggled(self, _selected: bool):
        self._refresh_button_text()
        self._refresh_group_checkboxes()

    def _refresh_button_text(self):
        all_selected = all(item.is_selected() for item in self._items)
        self.action_button.set_text(BUTTON_TEXT_DEFAULT if all_selected else BUTTON_TEXT_SELECTED)

    def _on_action_clicked(self):
        selected_paths = [
            f["path"] for f, item in zip(self._files, self._items) if item.is_selected()
        ]
        self.delete_requested.emit(selected_paths)
