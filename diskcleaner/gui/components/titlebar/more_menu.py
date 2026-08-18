from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from diskcleaner.gui.theme import palette_for
from diskcleaner.gui.typo import body_md, rem, ver

from . import styles


def _with_alpha(hex_color: str, alpha: int) -> QColor:
    color = QColor(hex_color)
    color.setAlpha(alpha)
    return color


class MoreMenu(QWidget):
    theme_toggle_requested = Signal()
    help_requested = Signal()
    license_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._is_dark = False
        self._bg_color = "#FFFFFF"
        self._separators = []

        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(0)

        self.theme_label = self._make_item("다크 모드")
        self.theme_label.mousePressEvent = lambda e: self._on_theme_click()
        self._layout.addWidget(self.theme_label)
        self._layout.addWidget(self._make_separator())

        self.help_label = self._make_item("도움말")
        self.help_label.mousePressEvent = lambda e: self._on_help_click()
        self._layout.addWidget(self.help_label)
        self._layout.addWidget(self._make_separator())

        self.license_label = self._make_item("라이센스")
        self.license_label.mousePressEvent = lambda e: self._on_license_click()
        self._layout.addWidget(self.license_label)

        self._gap_before_version = QWidget()
        self._layout.addWidget(self._gap_before_version)

        self.version_label = QLabel("버전 정보 : 1.0.0 ver")
        self.version_label.setObjectName("moreMenuVersion")
        self.version_label.setFont(ver())
        self.version_label.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self.version_label)

        self._bottom_padding = QWidget()
        self._layout.addWidget(self._bottom_padding)

        self.apply_theme(dark=False)
        self._apply_responsive_size()

    def _apply_responsive_size(self):
        self._menu_width = rem(styles.MENU_WIDTH_REM)
        self._corner_radius = rem(styles.CORNER_RADIUS_REM)
        self._triangle_size = rem(styles.TRIANGLE_SIZE_REM)
        self._shadow_margin = rem(styles.SHADOW_MARGIN_REM)
        self._shadow_y_offset = rem(styles.SHADOW_Y_OFFSET_REM)
        self._shadow_layers = [(rem(grow), alpha) for grow, alpha in styles.SHADOW_LAYERS_REM]

        item_height = rem(styles.ITEM_HEIGHT_REM)
        for label in (self.theme_label, self.help_label, self.license_label):
            label.setFixedHeight(item_height)

        separator_height = rem(styles.SEPARATOR_HEIGHT_REM)
        for separator in self._separators:
            separator.setFixedHeight(separator_height)

        self._gap_before_version.setFixedHeight(rem(styles.GAP_BEFORE_VERSION_REM))
        self._bottom_padding.setFixedHeight(rem(styles.BOTTOM_PADDING_REM))

        self._layout.setContentsMargins(
            self._shadow_margin,
            self._shadow_margin + self._triangle_size,
            self._shadow_margin,
            self._shadow_margin,
        )

        menu_height = (
            item_height * 3
            + separator_height * 2
            + self._gap_before_version.height()
            + self.version_label.sizeHint().height()
            + self._bottom_padding.height()
        )
        self.setFixedSize(
            self._menu_width + self._shadow_margin * 2,
            menu_height + self._triangle_size + self._shadow_margin * 2,
        )
        self.update()

    def _build_path(self, grow: float = 0, dy: float = 0) -> QPainterPath:
        path = QPainterPath()
        body_height = self.height() - self._triangle_size - self._shadow_margin * 2
        body_rect = QRectF(
            self._shadow_margin - grow,
            self._shadow_margin + self._triangle_size - grow + dy,
            self._menu_width + grow * 2,
            body_height + grow * 2,
        )
        path.addRoundedRect(body_rect, self._corner_radius + grow, self._corner_radius + grow)

        tip_x = self._shadow_margin + self._menu_width / 2
        triangle = QPainterPath()
        triangle.moveTo(
            tip_x - self._triangle_size - grow, self._shadow_margin + self._triangle_size + dy
        )
        triangle.lineTo(tip_x, self._shadow_margin - grow + dy)
        triangle.lineTo(
            tip_x + self._triangle_size + grow, self._shadow_margin + self._triangle_size + dy
        )
        triangle.closeSubpath()

        path.addPath(triangle)
        return path

    def _make_item(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("moreMenuItem")
        label.setFont(body_md())
        label.setAlignment(Qt.AlignCenter)
        label.setCursor(Qt.PointingHandCursor)
        return label

    def _make_separator(self) -> QFrame:
        line = QFrame()
        line.setObjectName("moreMenuSeparator")
        self._separators.append(line)
        return line

    def _on_theme_click(self):
        self.theme_toggle_requested.emit()
        self.close()

    def _on_help_click(self):
        self.help_requested.emit()
        self.close()

    def _on_license_click(self):
        self.license_requested.emit()
        self.close()

    def apply_theme(self, dark: bool):
        self._is_dark = dark
        p = palette_for(dark)

        self.theme_label.setText("라이트 모드" if dark else "다크 모드")
        text_color = p.text_primary
        line_color = p.border
        bg_color = p.bg
        self._bg_color = bg_color

        self.setStyleSheet(
            f"""
            QLabel#moreMenuItem {{
                color: {text_color};
                background: transparent;
            }}
            QLabel#moreMenuItem:hover {{
                background-color: {p.hover_overlay};
            }}
            QFrame#moreMenuSeparator {{
                background: {line_color};
            }}
            QLabel#moreMenuVersion {{
                color: {p.text_tertiary};
            }}
        """
        )
        self.update()

    def refresh_fonts(self):
        self.theme_label.setFont(body_md())
        self.help_label.setFont(body_md())
        self.license_label.setFont(body_md())
        self.version_label.setFont(ver())
        self._apply_responsive_size()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        p = palette_for(self._is_dark)

        painter.setPen(Qt.NoPen)
        for grow, alpha in self._shadow_layers:
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.drawPath(self._build_path(grow=grow, dy=self._shadow_y_offset))

        path = self._build_path()

        painter.setBrush(QColor(self._bg_color))
        painter.drawPath(path)

        painter.setPen(_with_alpha(p.border, 160))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        painter.end()

    def show_below(self, anchor_widget: QWidget):
        self._apply_responsive_size()

        anchor_global = anchor_widget.mapToGlobal(QPoint(0, anchor_widget.height()))
        anchor_center_x = anchor_global.x() + anchor_widget.width() / 2
        visible_box_x = anchor_center_x - self._menu_width / 2
        triangle_tip_y = anchor_global.y() + 4

        x = visible_box_x - self._shadow_margin
        y = triangle_tip_y - self._shadow_margin

        self.move(round(x), round(y))
        self.show()
