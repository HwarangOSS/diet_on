from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QFrame, QVBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon
from diskcleaner.gui.typo import titlebar_title

from . import icons
from .more_menu import MoreMenu

PADDING = 12
ICON_BUTTON_SIZE = 18

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
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(PADDING, PADDING, PADDING, PADDING)
        bar_layout.setSpacing(PADDING)

        self.title_label = QLabel(self._full_title)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setFont(titlebar_title())
        bar_layout.addWidget(self.title_label, alignment=Qt.AlignVCenter)
        bar_layout.addStretch()

        ICON_GAP = 3

        self.menu_button = self._make_icon_button(icons.make_more_icon, self.menu_requested)
        bar_layout.addWidget(self.menu_button, alignment=Qt.AlignVCenter)
        bar_layout.addSpacing(ICON_GAP)

        self.min_button = self._make_icon_button(icons.make_minimize_icon, self.minimize_requested)
        bar_layout.addWidget(self.min_button, alignment=Qt.AlignVCenter)
        bar_layout.addSpacing(ICON_GAP)

        self.close_button = self._make_icon_button(icons.make_close_icon, self.close_requested)
        bar_layout.addWidget(self.close_button, alignment=Qt.AlignVCenter)

        outer.addWidget(bar)

        self.separator = QFrame()
        self.separator.setObjectName("titleSeparator")
        self.separator.setFixedHeight(1)
        outer.addWidget(self.separator)

        # --- 더보기 팝업 메뉴 ---
        self.more_menu = MoreMenu(self)
        self.menu_button.clicked.disconnect()
        self.menu_button.clicked.connect(self._toggle_more_menu)

        self.more_menu.theme_toggle_requested.connect(self.menu_requested.emit)
        self.more_menu.help_requested.connect(lambda: print("[DEBUG] 도움말 클릭"))
        self.more_menu.license_requested.connect(lambda: print("[DEBUG] 라이센스 클릭"))

        self.apply_icon_colors(dark=False)

    def _make_icon_button(self, icon_factory, signal: Signal) -> QPushButton:
        button = QPushButton()
        button.setObjectName("titleIconButton")
        button.setFixedSize(ICON_BUTTON_SIZE, ICON_BUTTON_SIZE)
        button.setIconSize(QSize(ICON_BUTTON_SIZE, ICON_BUTTON_SIZE))
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
        color = "#FFFFFF" if dark else "#101820"
        self.menu_button.setIcon(QIcon(icons.make_more_icon(color)))
        self.min_button.setIcon(QIcon(icons.make_minimize_icon(color)))
        self.close_button.setIcon(QIcon(icons.make_close_icon(color)))

    def update_responsive_layout(self, container_width: int):
        self.menu_button.setVisible(container_width >= MORE_BUTTON_HIDE_WIDTH)

        if container_width < TITLE_COLLAPSE_WIDTH:
            metrics = self.title_label.fontMetrics()
            available = max(container_width - (PADDING * 2) - (ICON_BUTTON_SIZE * 3) - (PADDING * 2), 20)
            elided = metrics.elidedText(self._full_title, Qt.ElideRight, available)
            self.title_label.setText(elided)
        else:
            self.title_label.setText(self._full_title)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)
