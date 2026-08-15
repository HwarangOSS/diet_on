from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


class TriStateCheckBox(QWidget):

    clicked = Signal()

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self._text = text
        self._state = Qt.Unchecked
        self._color = "#3A4A63"
        self._base_box_size = 12
        self._base_gap = 6
        self._box_size = self._base_box_size
        self._gap = self._base_gap
        self.setCursor(Qt.PointingHandCursor)

    def setCheckState(self, state):
        if self._state == state:
            return
        self._state = state
        self.updateGeometry()
        self.update()

    def checkState(self):
        return self._state

    def set_color(self, color: str):
        self._color = color
        self.update()

    def set_scale(self, scale: float):
        self._box_size = max(8, round(self._base_box_size * scale))
        self._gap = max(2, round(self._base_gap * scale))
        self.updateGeometry()
        self.update()

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        text_w = fm.horizontalAdvance(self._text) if self._text else 0
        w = self._box_size + (self._gap + text_w if self._text else 0)
        h = max(self._box_size, fm.height())
        return QSize(w, h)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        box_size = self._box_size
        y = (self.height() - box_size) / 2
        rect = QRectF(0, y, box_size, box_size)
        color = QColor(self._color)

        if self._state != Qt.Unchecked:
            pen = QPen(color)
            pen.setWidthF(max(1.4, box_size * 0.16))
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            if self._state == Qt.Checked:
                glyph = QPainterPath()
                glyph.moveTo(rect.left() + box_size * 0.10, rect.top() + box_size * 0.55)
                glyph.lineTo(rect.left() + box_size * 0.40, rect.top() + box_size * 0.82)
                glyph.lineTo(rect.left() + box_size * 0.92, rect.top() + box_size * 0.20)
                painter.drawPath(glyph)
            else:
                painter.drawLine(
                    QPointF(rect.left() + box_size * 0.08, rect.center().y()),
                    QPointF(rect.left() + box_size * 0.92, rect.center().y()),
                )

        if self._text:
            painter.setPen(QColor(self._color))
            painter.setFont(self.font())
            text_rect = QRectF(box_size + self._gap, 0, self.width() - box_size - self._gap, self.height())
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, self._text)

        painter.end()
