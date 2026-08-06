from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import QWidget

from diskcleaner.gui.theme import palette_for

BAR_WIDTH = 513
BAR_HEIGHT = 22
RADIUS = BAR_HEIGHT / 2


def _with_alpha(hex_color: str, alpha: int) -> QColor:
    color = QColor(hex_color)
    color.setAlpha(alpha)
    return color


class LoadingProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(BAR_WIDTH, BAR_HEIGHT)

        self._progress = 0.0
        self._is_dark = False

        self._anim = QPropertyAnimation(self, b"progress")
        self._anim.setDuration(300)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def _get_progress(self):
        return self._progress

    def _set_progress(self, value):
        self._progress = value
        self.update()

    progress = Property(float, _get_progress, _set_progress)

    # API
    def set_progress(self, value: float, animated: bool = True):
        value = max(0.0, min(100.0, value))

        if animated:
            self._anim.stop()
            self._anim.setStartValue(self._progress)
            self._anim.setEndValue(value)
            self._anim.start()
        else:
            self._progress = value
            self.update()

    def set_dark(self, dark: bool):
        self._is_dark = dark
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        p = palette_for(self._is_dark)

        track_path = QPainterPath()
        track_rect = QRectF(0, 0, self.width(), self.height())
        track_path.addRoundedRect(track_rect, RADIUS, RADIUS)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(p.bg))
        painter.drawPath(track_path)

        painter.setPen(_with_alpha(p.primary, 128))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(track_path)

        fill_ratio = self._progress / 100.0
        fill_width = self.width() * fill_ratio

        if fill_width > 0:
            painter.setClipPath(track_path)

            fill_path = QPainterPath()
            fill_rect = QRectF(0, 0, fill_width, self.height())
            fill_path.addRoundedRect(fill_rect, RADIUS, RADIUS)

            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(p.primary))
            painter.drawPath(fill_path)

        painter.end()
