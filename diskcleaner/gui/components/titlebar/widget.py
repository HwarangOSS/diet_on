from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from diskcleaner.gui.theme import palette_for
from diskcleaner.gui.typo import FontFamily, get_font, rem

from . import icons
from .more_menu import MoreMenu


PADDING_REM = 0.5 
ICON_BUTTON_SIZE_REM = 1.125
ICON_GAP_REM = 0.1875 
TITLE_FONT_PT = 15  

def _title_font():
    return get_font(FontFamily.PLAY_REGULAR, TITLE_FONT_PT, role="headline")

TITLE_COLLAPSE_WIDTH = 250
MORE_BUTTON_HIDE_WIDTH = 250


class TitleBar(QWidget):
    minimize_requested = Signal()
    close_requested = Signal()
    menu_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("titleBar")

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self._drag_pos = None
        self._is_dark = False
        self._full_title = "DietOn"

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        bar = QWidget()
        bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self._bar_layout = QHBoxLayout(bar)

        self.title_label = QLabel(self._full_title)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setFont(_title_font())
        self._bar_layout.addWidget(self.title_label, alignment=Qt.AlignVCenter)
        self._bar_layout.addStretch()

        self.menu_button = self._make_icon_button(icons.make_more_icon, self.menu_requested)
        self._bar_layout.addWidget(self.menu_button, alignment=Qt.AlignVCenter)
        self._bar_layout.addSpacing(0)
        self._icon_gap_spacer_1 = self._bar_layout.itemAt(self._bar_layout.count() - 1).spacerItem()

        self.min_button = self._make_icon_button(icons.make_minimize_icon, self.minimize_requested)
        self._bar_layout.addWidget(self.min_button, alignment=Qt.AlignVCenter)
        self._bar_layout.addSpacing(0)
        self._icon_gap_spacer_2 = self._bar_layout.itemAt(self._bar_layout.count() - 1).spacerItem()

        self.close_button = self._make_icon_button(icons.make_close_icon, self.close_requested)
        self._bar_layout.addWidget(self.close_button, alignment=Qt.AlignVCenter)

        outer.addWidget(bar)

        self.separator = QFrame()
        self.separator.setObjectName("titleSeparator")
        self.separator.setFixedHeight(1)
        outer.addWidget(self.separator)

        self.more_menu = MoreMenu(self)
        self.menu_button.clicked.disconnect()
        self.menu_button.clicked.connect(self._toggle_more_menu)

        self.more_menu.theme_toggle_requested.connect(self.menu_requested.emit)
        self.more_menu.help_requested.connect(lambda: print("[DEBUG] 도움말 클릭"))
        self.more_menu.license_requested.connect(lambda: print("[DEBUG] 라이센스 클릭"))

        self._apply_responsive_size()

    def _make_icon_button(self, icon_factory, signal: Signal) -> QPushButton:
        button = QPushButton()
        button.setObjectName("titleIconButton")
        button.setCursor(Qt.PointingHandCursor)
        button.setFlat(True)
        button.clicked.connect(signal.emit)
        button.setProperty("icon_factory", icon_factory)
        return button

    def _toggle_more_menu(self):
        if self.more_menu.isVisible():
            self.more_menu.close()
        else:
            self.more_menu.apply_theme(dark=self._is_dark)
            self.more_menu.show_below(self.menu_button)

    def apply_icon_colors(self, dark: bool):
        self._is_dark = dark
        color = palette_for(dark).text_primary
        size = rem(ICON_BUTTON_SIZE_REM)
        self.menu_button.setIcon(QIcon(icons.make_more_icon(color, size=size)))
        self.min_button.setIcon(QIcon(icons.make_minimize_icon(color, size=size)))
        self.close_button.setIcon(QIcon(icons.make_close_icon(color, size=size)))

    def _apply_responsive_size(self):
        padding = rem(PADDING_REM)
        self._bar_layout.setContentsMargins(padding, padding, padding, padding)
        self._bar_layout.setSpacing(padding)

        icon_gap = rem(ICON_GAP_REM)
        self._icon_gap_spacer_1.changeSize(icon_gap, 0, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self._icon_gap_spacer_2.changeSize(icon_gap, 0, QSizePolicy.Fixed, QSizePolicy.Minimum)

        size = rem(ICON_BUTTON_SIZE_REM)
        for button in (self.menu_button, self.min_button, self.close_button):
            button.setFixedSize(size, size)
            button.setIconSize(QSize(size, size))

        self.apply_icon_colors(self._is_dark)
        self._bar_layout.invalidate()

    def update_responsive_layout(self, container_width: int):
        self.menu_button.setVisible(container_width >= MORE_BUTTON_HIDE_WIDTH)

        if container_width < TITLE_COLLAPSE_WIDTH:
            padding = rem(PADDING_REM)
            icon_button_size = rem(ICON_BUTTON_SIZE_REM)
            metrics = self.title_label.fontMetrics()
            available = max(
                container_width - (padding * 2) - (icon_button_size * 3) - (padding * 2), 20
            )
            elided = metrics.elidedText(self._full_title, Qt.ElideRight, available)
            self.title_label.setText(elided)
        else:
            self.title_label.setText(self._full_title)

    def refresh_fonts(self):
        self.title_label.setFont(_title_font())
        self._apply_responsive_size()
        self.more_menu.refresh_fonts()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            )
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)
