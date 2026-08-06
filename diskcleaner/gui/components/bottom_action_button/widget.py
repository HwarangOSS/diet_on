from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPointF,
    QPropertyAnimation,
    QRectF,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from diskcleaner.gui.theme import LIGHT
from diskcleaner.gui.typo import BASE_WINDOW_WIDTH, headline_small

from . import styles


class BottomActionButton(QWidget):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("bottomActionButton")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)

        self._is_dark = False
        self._hovered = False
        self._pressed = False
        self._text = ""
        self._scale = 1.0

        self._scale_anim = QPropertyAnimation(self, b"scale")
        self._scale_anim.setDuration(styles.ANIM_DURATION_MS)
        self._scale_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.setFixedSize(styles.BASE_WIDTH, styles.BASE_HEIGHT)

    def _get_scale(self):
        return self._scale

    def _set_scale(self, value):
        self._scale = value
        self.update()

    scale = Property(float, _get_scale, _set_scale)

    # API
    def set_text(self, text: str):
        self._text = text
        self.update()

    def set_dark(self, dark: bool):
        self._is_dark = dark
        self.update()

    def update_responsive_size(self, container_width: int):
        scale = container_width / BASE_WINDOW_WIDTH
        scale = max(styles.SCALE_MIN, min(scale, styles.SCALE_MAX))
        self.setFixedSize(container_width, round(styles.BASE_HEIGHT * scale))

    # 이벤트
    def enterEvent(self, event):
        self._hovered = True
        self._animate_to(styles.HOVER_SCALE)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        if not self._pressed:
            self._animate_to(1.0)
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self._animate_to(styles.HOVER_SCALE)
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._pressed:
            self._pressed = False
            if not self._hovered:
                self._animate_to(1.0)
            if self.rect().contains(event.position().toPoint()):
                self.clicked.emit()
            self.update()
        super().mouseReleaseEvent(event)

    def _animate_to(self, target: float):
        self._scale_anim.stop()
        self._scale_anim.setStartValue(self._scale)
        self._scale_anim.setEndValue(target)
        self._scale_anim.start()

    # 내부
    def _is_active(self) -> bool:
        return self._hovered or self._pressed

    def _background_color(self) -> QColor:
        active = self._is_active()
        if self._is_dark:
            return QColor(styles.DARK_ACTIVE_BG if active else styles.DARK_IDLE_BG)
        if active:
            return QColor(styles.LIGHT_ACTIVE_BG)
        color = QColor(LIGHT.primary)
        color.setAlpha(styles.LIGHT_IDLE_ALPHA)
        return color

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()

        # 호버 애니메이션
        painter.save()
        pivot = QPointF(w / 2, h)
        painter.translate(pivot)
        painter.scale(self._scale, self._scale)
        painter.translate(-pivot)

        clip = QPainterPath()
        clip.addRect(QRectF(0, 0, w, h))
        painter.setClipPath(clip)

        dome = QPainterPath()
        dome.addEllipse(QRectF(0, 0, w, h * 2))
        painter.fillPath(dome, self._background_color())
        layers = 6
        max_width = styles.GLOW_SPREAD * 2
        for i in range(layers):
            t = i / (layers - 1)
            pen_width = max(1, round(max_width * (1 - t)))
            alpha = int(styles.GLOW_ALPHA * (1 - t))
            pen = QPen(QColor(255, 255, 255, alpha))
            pen.setWidthF(pen_width)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(dome)

        if self._text:
            painter.setPen(QColor("#FFFFFF"))
            painter.setFont(headline_small())
            text_rect = QRectF(0, 0, w, h * 0.6)
            painter.drawText(text_rect, Qt.AlignHCenter | Qt.AlignTop, self._text)

        painter.restore()
        painter.end()
