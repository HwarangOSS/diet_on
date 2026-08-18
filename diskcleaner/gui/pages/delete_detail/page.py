from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from diskcleaner.gui.components.bottom_action_button import BottomActionButton
from diskcleaner.gui.components.file_list_item import FileListItem
from diskcleaner.gui.components.side_action_button import SideActionButton
from diskcleaner.gui.components.tri_state_checkbox import TriStateCheckBox
from diskcleaner.gui.result_mapping import REVIEW_CATEGORY_LABEL
from diskcleaner.gui.theme import palette_for
from diskcleaner.gui.typo import FontFamily, get_font

from . import styles

BUTTON_TEXT_DEFAULT = "전체 삭제"
BUTTON_TEXT_SELECTED = "선택 삭제"

BACK_BUTTON_TEXT = "Back"
SELECT_ALL_TEXT = "전체 선택"


def _design_scale(container_width: int) -> float:
    return container_width / styles.REFERENCE_WIDTH


def _title_font(scale: float):
    return get_font(FontFamily.PLAY_REGULAR, 22, role="headline_small", scale=scale)


def _label_font(scale: float):
    return get_font(FontFamily.PRETENDARD_REGULAR, 7, role="body_mini", scale=scale)


class DeletePage(QWidget):
    delete_requested = Signal(list)
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("deletePage")

        self._items: list[FileListItem] = []
        self._files: list[dict] = []
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

        self.title_label = QLabel("Delete")
        self.title_label.setObjectName("detailTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        select_all_row = QHBoxLayout()
        select_all_row.addStretch()
        self.select_all_checkbox = TriStateCheckBox(SELECT_ALL_TEXT)
        self.select_all_checkbox.setObjectName("deleteSelectAllCheckbox")
        self.select_all_checkbox.clicked.connect(self._toggle_select_all)
        select_all_row.addWidget(self.select_all_checkbox)
        layout.addLayout(select_all_row)
        self._select_all_row = select_all_row

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("detailScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

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

        self.update_responsive_size(styles.REFERENCE_WIDTH)

    # API
    def set_files(self, files: list[dict]):
        for item in self._items:
            self.list_layout.removeWidget(item)
            item.setParent(None)
            item.deleteLater()
        self._items.clear()
        self._files = list(files)

        insert_at = self.list_layout.count() - 1
        for f in files:
            item = FileListItem()
            item.set_file(f["name"], f["path"], f["size_bytes"], f.get("reason"))
            item.set_selected(f.get("category") != REVIEW_CATEGORY_LABEL, emit=False)
            item.set_dark(self._is_dark)
            item.toggled.connect(self._on_item_toggled)
            self.list_layout.insertWidget(insert_at, item)
            insert_at += 1
            self._items.append(item)

        self.update_responsive_size(self.width() or styles.REFERENCE_WIDTH)
        self._refresh_button_text()
        self._refresh_select_all_checkbox()

    def apply_theme(self, dark: bool):
        self._is_dark = dark
        for item in self._items:
            item.set_dark(dark)
        self.action_button.set_dark(dark)
        self.back_button.set_dark(dark)
        self.select_all_checkbox.set_color(palette_for(dark).primary)

    def update_responsive_size(self, container_width: int):
        scale = _design_scale(container_width)

        self.title_label.setFont(_title_font(scale))
        self.select_all_checkbox.setFont(_label_font(scale))
        self.select_all_checkbox.set_scale(scale)

        margin = round(styles.REF_MARGIN * scale)
        margin_top = round(styles.REF_MARGIN_TOP * scale)
        margin_bottom = round(styles.REF_MARGIN_BOTTOM * scale)
        self._layout.setContentsMargins(margin, margin_top, margin, margin_bottom)
        self._layout.setSpacing(round(styles.REF_PAGE_GAP * scale))
        self.list_layout.setSpacing(round(styles.REF_LIST_GAP * scale))
        self._select_all_row.setContentsMargins(0, 0, 0, round(styles.REF_SELECT_ALL_GAP * scale))

        back_button_width = self.back_button.width()
        content_width = max(1, container_width - back_button_width - 2 * margin)
        self._right_spacer.setFixedWidth(back_button_width)

        for item in self._items:
            item.update_responsive_size(container_width)
        self.action_button.update_responsive_size(
            round(content_width * styles.ACTION_BUTTON_WIDTH_SCALE),
            scale=scale,
            height_scale=styles.ACTION_BUTTON_HEIGHT_SCALE,
            text_size=styles.ACTION_BUTTON_TEXT_SIZE,
        )
        self.back_button.update_responsive_size(self.height(), scale=scale)

    def refresh_fonts(self):
        self.update_responsive_size(self.width() or styles.REFERENCE_WIDTH)
        for item in self._items:
            item.refresh_fonts()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_responsive_size(self.width())

    # 내부
    def _toggle_select_all(self):
        select_all = not all(item.is_selected() for item in self._items)
        for item in self._items:
            item.set_selected(select_all, emit=False)
        self._refresh_button_text()
        self._refresh_select_all_checkbox()

    def _refresh_select_all_checkbox(self):
        states = [item.is_selected() for item in self._items]
        checkbox = self.select_all_checkbox
        checkbox.blockSignals(True)
        if not states:
            checkbox.setCheckState(Qt.Unchecked)
        elif all(states):
            checkbox.setCheckState(Qt.Checked)
        elif not any(states):
            checkbox.setCheckState(Qt.Unchecked)
        else:
            checkbox.setCheckState(Qt.PartiallyChecked)
        checkbox.blockSignals(False)

    def _on_item_toggled(self, _selected: bool):
        self._refresh_button_text()
        self._refresh_select_all_checkbox()

    def _refresh_button_text(self):
        all_selected = all(item.is_selected() for item in self._items)
        self.action_button.set_text(BUTTON_TEXT_DEFAULT if all_selected else BUTTON_TEXT_SELECTED)

    def _on_action_clicked(self):
        selected_paths = [
            f["path"] for f, item in zip(self._files, self._items) if item.is_selected()
        ]
        self.delete_requested.emit(selected_paths)
