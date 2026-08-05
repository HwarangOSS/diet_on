from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QPainter, QPainterPath
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from diskcleaner.gui.typo import body_medium, caption

MENU_WIDTH = 92
MENU_HEIGHT = 150
CORNER_RADIUS = 8
TRIANGLE_SIZE = 8
TRIANGLE_OFFSET = 18


class MoreMenu(QWidget):
    theme_toggle_requested = Signal()
    help_requested = Signal()
    license_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(MENU_WIDTH, MENU_HEIGHT + TRIANGLE_SIZE)

        self._is_dark = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, TRIANGLE_SIZE, 0, 0)
        layout.setSpacing(0)

        self.theme_label = self._make_item("다크 모드")
        self.theme_label.mousePressEvent = lambda e: self._on_theme_click()
        layout.addWidget(self.theme_label)
        layout.addWidget(self._make_separator())

        self.help_label = self._make_item("도움말")
        self.help_label.mousePressEvent = lambda e: self._on_help_click()
        layout.addWidget(self.help_label)
        layout.addWidget(self._make_separator())

        self.license_label = self._make_item("라이센스")
        self.license_label.mousePressEvent = lambda e: self._on_license_click()
        layout.addWidget(self.license_label)

        layout.addStretch()

        self.version_label = QLabel("버전 정보 : 1.0.0 ver")
        self.version_label.setObjectName("moreMenuVersion")
        self.version_label.setFont(caption())
        self.version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.version_label)
        layout.addSpacing(10)

        self.apply_theme(dark=False)

    def _make_item(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("moreMenuItem")
        label.setFont(body_medium())
        label.setAlignment(Qt.AlignCenter)
        label.setFixedHeight(34)
        label.setCursor(Qt.PointingHandCursor)
        return label

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

        self.theme_label.setText("라이트 모드" if dark else "다크 모드")

        text_color = "#FFFFFF" if dark else "#555555"
        line_color = "#B9B9B9"
        bg_color = "#1A2332" if dark else "#FFFFFF"

        self._bg_color = bg_color

        self.setStyleSheet(
            f"""
            QLabel#moreMenuItem {{
                color: {text_color};
                background: transparent;
            }}
            QLabel#moreMenuItem:hover {{
                background-color: rgba(0, 0, 0, {0.08 if not dark else 0.15});
            }}
            QFrame#moreMenuSeparator {{
                background: {line_color};
            }}
            QLabel#moreMenuVersion {{
                color: #B9B9B9;
            }}
        """
        )
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        body_rect = QRectF(0, TRIANGLE_SIZE, MENU_WIDTH, MENU_HEIGHT)
        path.addRoundedRect(body_rect, CORNER_RADIUS, CORNER_RADIUS)

        tip_x = MENU_WIDTH - TRIANGLE_OFFSET
        triangle = QPainterPath()
        triangle.moveTo(tip_x - TRIANGLE_SIZE, TRIANGLE_SIZE)
        triangle.lineTo(tip_x, 0)
        triangle.lineTo(tip_x + TRIANGLE_SIZE, TRIANGLE_SIZE)
        triangle.closeSubpath()

        path.addPath(triangle)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(self._bg_color))
        painter.drawPath(path)

        painter.setPen(QColor(0, 0, 0, 20))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        painter.end()

    def show_below(self, anchor_widget: QWidget):
        anchor_global = anchor_widget.mapToGlobal(QPoint(0, anchor_widget.height()))
        x = anchor_global.x() + anchor_widget.width() - MENU_WIDTH
        y = anchor_global.y() + 4
        self.move(x, y)
        self.show()
