from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from diskcleaner.gui.theme import palette_for
from diskcleaner.gui.typo import body_md, get_global_scale, ver

BASE_MENU_WIDTH = 92
BASE_ITEM_HEIGHT = 34
BASE_CORNER_RADIUS = 8
BASE_TRIANGLE_SIZE = 8
BASE_TRIANGLE_OFFSET = 18
BASE_VERSION_SPACING = 10

SCALE_MIN = 0.6
SCALE_MAX = 1.5

MENU_WIDTH = BASE_MENU_WIDTH
MENU_HEIGHT = BASE_ITEM_HEIGHT * 3 + BASE_VERSION_SPACING + 20


def _with_alpha(hex_color: str, alpha: int) -> QColor:
    color = QColor(hex_color)
    color.setAlpha(alpha)
    return color


class MoreMenu(QWidget):
    theme_toggle_requested = Signal()
    help_requested = Signal()
    license_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._is_dark = False
        self._bg_color = "#FFFFFF"
        self._scale = 1.0
        self._menu_width = BASE_MENU_WIDTH
        self._triangle_size = BASE_TRIANGLE_SIZE
        self._corner_radius = BASE_CORNER_RADIUS

        self._outer_layout = QVBoxLayout(self)
        self._outer_layout.setContentsMargins(0, BASE_TRIANGLE_SIZE, 0, 0)
        self._outer_layout.setSpacing(0)

        self.theme_label = self._make_item("다크 모드")
        self.theme_label.mousePressEvent = lambda e: self._on_theme_click()
        self._outer_layout.addWidget(self.theme_label)
        self.sep1 = self._make_separator()
        self._outer_layout.addWidget(self.sep1)

        self.help_label = self._make_item("도움말")
        self.help_label.mousePressEvent = lambda e: self._on_help_click()
        self._outer_layout.addWidget(self.help_label)
        self.sep2 = self._make_separator()
        self._outer_layout.addWidget(self.sep2)

        self.license_label = self._make_item("라이센스")
        self.license_label.mousePressEvent = lambda e: self._on_license_click()
        self._outer_layout.addWidget(self.license_label)

        self._outer_layout.addStretch()

        self.version_label = QLabel("버전 정보 : 1.0.0 ver")
        self.version_label.setObjectName("moreMenuVersion")
        self.version_label.setFont(ver())
        self.version_label.setAlignment(Qt.AlignCenter)
        self._outer_layout.addWidget(self.version_label)
        self._version_spacer_size = BASE_VERSION_SPACING
        self._outer_layout.addSpacing(self._version_spacer_size)

        self._items = [self.theme_label, self.help_label, self.license_label]

        self.apply_theme(dark=False)
        self._apply_responsive_size()

    def _make_item(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("moreMenuItem")
        label.setFont(body_md())
        label.setAlignment(Qt.AlignCenter)
        label.setFixedHeight(BASE_ITEM_HEIGHT)
        label.setCursor(Qt.PointingHandCursor)
        return label

    def refresh_fonts(self):
        """전역 폰트 스케일이 바뀌면 팝업 자체 크기도 같이 맞춰서, 커진 글자가
        고정폭 92px 밖으로 넘치지 않게 함."""
        self.theme_label.setFont(body_md())
        self.help_label.setFont(body_md())
        self.license_label.setFont(body_md())
        self.version_label.setFont(ver())
        self._apply_responsive_size()

    def _apply_responsive_size(self):
        scale = max(SCALE_MIN, min(get_global_scale(), SCALE_MAX))
        self._scale = scale

        self._menu_width = round(BASE_MENU_WIDTH * scale)
        item_height = round(BASE_ITEM_HEIGHT * scale)
        self._triangle_size = max(4, round(BASE_TRIANGLE_SIZE * scale))
        self._corner_radius = round(BASE_CORNER_RADIUS * scale)
        version_spacing = round(BASE_VERSION_SPACING * scale)

        for label in self._items:
            label.setFixedHeight(item_height)

        self._outer_layout.setContentsMargins(0, self._triangle_size, 0, 0)
        # 마지막 addSpacing으로 넣은 항목을 다시 만들 수는 없어서, 대신 버전
        # 라벨에 하단 여백을 준다.
        self.version_label.setContentsMargins(0, 0, 0, version_spacing)

        menu_height = item_height * 3 + self.version_label.sizeHint().height() + version_spacing
        self.setFixedSize(self._menu_width, menu_height + self._triangle_size)
        self.update()

    def _make_separator(self) -> QFrame:
        line = QFrame()
        line.setObjectName("moreMenuSeparator")
        line.setFixedHeight(1)
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
        bg_color = p.surface
        self._bg_color = bg_color

        self.setStyleSheet(f"""
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
        """)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        p = palette_for(self._is_dark)

        menu_width = self.width()
        menu_height = self.height() - self._triangle_size
        triangle_offset = round(BASE_TRIANGLE_OFFSET * self._scale)

        path = QPainterPath()
        body_rect = QRectF(0, self._triangle_size, menu_width, menu_height)
        path.addRoundedRect(body_rect, self._corner_radius, self._corner_radius)

        tip_x = menu_width - triangle_offset
        triangle = QPainterPath()
        triangle.moveTo(tip_x - self._triangle_size, self._triangle_size)
        triangle.lineTo(tip_x, 0)
        triangle.lineTo(tip_x + self._triangle_size, self._triangle_size)
        triangle.closeSubpath()

        path.addPath(triangle)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(self._bg_color))
        painter.drawPath(path)

        painter.setPen(_with_alpha(p.border, 160))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        painter.end()

    def show_below(self, anchor_widget: QWidget):
        self._apply_responsive_size()
        anchor_global = anchor_widget.mapToGlobal(QPoint(0, anchor_widget.height()))
        x = anchor_global.x() + anchor_widget.width() - self.width()
        y = anchor_global.y() + 4
        self.move(x, y)
        self.show()
