from PySide6.QtCore import Property, QEasingCurve, QPointF, QPropertyAnimation, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QRadialGradient
from PySide6.QtWidgets import QWidget

from . import styles
from .icons import load_icon_renderers


class PowerButton(QWidget):
    toggled = Signal(bool)
    clicked_scan = Signal()

    def __init__(self, parent=None, size: int = styles.DEFAULT_BUTTON_SIZE):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)

        self._is_active = False
        self._svg_inactive, self._svg_active = load_icon_renderers()

        # --- 애니메이션 ---
        self._scale = 1.0
        self._scale_anim = QPropertyAnimation(self, b"scale")
        self._scale_anim.setDuration(styles.PRESS_ANIM_DURATION_MS)
        self._scale_anim.setEasingCurve(QEasingCurve.OutBack)

    def _get_scale(self):
        return self._scale

    def _set_scale(self, value):
        self._scale = value
        self.update()

    scale = Property(float, _get_scale, _set_scale)

    # 반응형
    def update_responsive_size(self, canvas_size: int):
        if canvas_size < styles.MIN_RESPONSIVE_CANVAS:
            self.hide()
            return

        self.show()
        new_size = max(1, round(canvas_size * styles.BUTTON_RATIO))
        if new_size != self.width():
            self.setFixedSize(new_size, new_size)

    # API : 연결 예정/일단 boolean 값
    @property
    def is_active(self) -> bool:
        return self._is_active

    def set_active(self, value: bool, emit: bool = True):
        if self._is_active == value:
            return
        self._is_active = value
        self.update()
        if emit:
            self.toggled.emit(self._is_active)

    # 이벤트
    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return super().mousePressEvent(event)

        self._is_active = not self._is_active
        self.toggled.emit(self._is_active)
        self.clicked_scan.emit()

        self._scale_anim.stop()
        self._scale = styles.PRESS_SCALE
        self._scale_anim.setStartValue(styles.PRESS_SCALE)
        self._scale_anim.setEndValue(1.0)
        self._scale_anim.start()

        self.update()
        super().mousePressEvent(event)

    # 디자인
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        radius = min(w, h) / 2.0
        center = QPointF(w / 2.0, h / 2.0)

        painter.save()
        painter.translate(center)
        painter.scale(self._scale, self._scale)
        painter.translate(-center)

        self._paint_background(painter, center, radius)
        self._paint_icon(painter, center, radius)

        painter.restore()
        painter.end()

    def _paint_background(self, painter: QPainter, center: QPointF, radius: float):
        # 배경 원
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(styles.BG_COLOR))
        painter.drawEllipse(center, radius, radius)

        gradient = QRadialGradient(center, radius)
        gradient.setColorAt(0.0, QColor(255, 255, 255, 0))
        gradient.setColorAt(styles.GLOW_INNER_STOP, QColor(255, 255, 255, 0))
        gradient.setColorAt(styles.GLOW_OUTER_STOP, styles.GLOW_COLOR)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(center, radius, radius)

    def _paint_icon(self, painter: QPainter, center: QPointF, radius: float):
        icon_size = radius * 2 * styles.ICON_RATIO
        icon_rect = QRectF(
            center.x() - icon_size / 2,
            center.y() - icon_size / 2,
            icon_size,
            icon_size,
        )
        renderer = self._svg_active if self._is_active else self._svg_inactive
        renderer.render(painter, icon_rect)
