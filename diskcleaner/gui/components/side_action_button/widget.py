from PySide6.QtCore import Property, QEasingCurve, QPointF, QPropertyAnimation, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QRadialGradient
from PySide6.QtWidgets import QWidget

from diskcleaner.gui.theme import LIGHT
from diskcleaner.gui.typo import body_mini, rem

from . import styles


class SideActionButton(QWidget):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sideActionButton")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)

        self._is_dark = False
        self._hovered = False
        self._pressed = False
        self._text = ""
        self._scale = 1.0
        self._design_scale = None
        self._visible_w = rem(styles.VISIBLE_WIDTH_REM)
        self._diameter = rem(styles.DIAMETER_REM)
        self._pad_x = 0
        self._pad_y = 0

        self._scale_anim = QPropertyAnimation(self, b"scale")
        self._scale_anim.setDuration(styles.ANIM_DURATION_MS)
        self._scale_anim.setEasingCurve(QEasingCurve.OutCubic)

        self._apply_size()

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

    def update_responsive_size(self, container_height: int, scale: float | None = None):
        self._design_scale = scale
        self._visible_w = rem(styles.VISIBLE_WIDTH_REM, scale=scale)
        self._diameter = rem(styles.DIAMETER_REM, scale=scale)
        self._apply_size()

    def _apply_size(self):
        grow = styles.HOVER_SCALE - 1.0
        self._pad_x = max(2, round(self._visible_w * grow) + 2)
        self._pad_y = max(2, round((self._diameter / 2) * grow) + 2)
        self.setFixedSize(self._visible_w + self._pad_x, self._diameter + 2 * self._pad_y)

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
        diameter = self._diameter
        visible_right = w - self._pad_x

        painter.save()
        pivot = QPointF(0, h / 2)
        painter.translate(pivot)
        painter.scale(self._scale, self._scale)
        painter.translate(-pivot)

        clip = QPainterPath()
        clip.addRect(QRectF(0, 0, w, h))
        painter.setClipPath(clip)

        circle_rect = QRectF(visible_right - diameter, (h - diameter) / 2, diameter, diameter)
        dome = QPainterPath()
        dome.addEllipse(circle_rect)
        painter.fillPath(dome, self._background_color())

        center = circle_rect.center()
        radius = diameter / 2
        gradient = QRadialGradient(center, radius)
        gradient.setColorAt(0.0, QColor(255, 255, 255, 0))
        gradient.setColorAt(styles.GLOW_INNER_STOP, QColor(255, 255, 255, 0))
        gradient.setColorAt(styles.GLOW_OUTER_STOP, QColor(255, 255, 255, styles.GLOW_ALPHA))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawPath(dome)

        if self._text:
            painter.setPen(QColor("#FFFFFF"))
            painter.setFont(body_mini())
            text_rect = QRectF(0, 0, visible_right, h)
            painter.drawText(text_rect, Qt.AlignCenter, self._text)

        painter.restore()
        painter.end()
