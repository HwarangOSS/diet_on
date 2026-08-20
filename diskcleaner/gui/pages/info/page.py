from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from diskcleaner.gui.components.side_action_button import SideActionButton
from diskcleaner.gui.typo import FontFamily, get_font

from . import styles

BACK_BUTTON_TEXT = "Back"


def _title_font(scale: float | None = None):
    return get_font(FontFamily.PLAY_REGULAR, styles.TITLE_FONT_PT, role="headline_small", scale=scale)


def _body_font(scale: float | None = None):
    return get_font(FontFamily.PRETENDARD_REGULAR, styles.BODY_FONT_PT, role="body", scale=scale)


def _design_scale(container_width: int) -> float:
    return container_width / styles.REFERENCE_WIDTH


class InfoPage(QWidget):
    """도움말 / 라이센스 같은 정적 텍스트를 앱 테마에 맞춰 보여주는 범용 페이지."""

    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("infoPage")

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

        self.title_label = QLabel()
        self.title_label.setObjectName("detailTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(_title_font())
        layout.addWidget(self.title_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("detailScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.body_label = QLabel()
        self.body_label.setObjectName("infoBody")
        self.body_label.setWordWrap(True)
        self.body_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.body_label.setFont(_body_font())
        self.body_label.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setWidget(self.body_label)
        layout.addWidget(self.scroll_area, stretch=1)

        self.update_responsive_size(styles.REFERENCE_WIDTH)

    # API
    def set_content(self, title: str, body: str):
        self.title_label.setText(title)
        self.body_label.setText(body)

    def apply_theme(self, dark: bool):
        self.back_button.set_dark(dark)

    def refresh_fonts(self):
        self.update_responsive_size(self.width() or styles.REFERENCE_WIDTH)

    def update_responsive_size(self, container_width: int):
        scale = _design_scale(container_width)

        self.title_label.setFont(_title_font(scale))
        self.body_label.setFont(_body_font(scale))

        margin = round(styles.REF_MARGIN * scale)
        margin_top = round(styles.REF_MARGIN_TOP * scale)
        self._layout.setContentsMargins(margin, margin_top, margin, margin_top)
        self._layout.setSpacing(round(styles.REF_PAGE_GAP * scale))

        back_button_width = self.back_button.width()
        self._right_spacer.setFixedWidth(back_button_width)
        self.back_button.update_responsive_size(self.height(), scale=scale)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_responsive_size(self.width())
