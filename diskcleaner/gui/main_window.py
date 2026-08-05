from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QPoint

BORDER_WIDTH = 6 

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setMouseTracking(True)

        self.resize(500, 500)
        self.setMinimumSize(250, 250)

        self._resizing = False
        self._resize_edge = None
        self._start_pos = None
        self._start_geo = None

    def _edge_at(self, pos: QPoint) -> str | None:
        rect = self.rect()
        left = pos.x() <= BORDER_WIDTH
        right = pos.x() >= rect.width() - BORDER_WIDTH
        top = pos.y() <= BORDER_WIDTH
        bottom = pos.y() >= rect.height() - BORDER_WIDTH

        if top and left: return "top_left"
        if top and right: return "top_right"
        if bottom and left: return "bottom_left"
        if bottom and right: return "bottom_right"
        if left: return "left"
        if right: return "right"
        if top: return "top"
        if bottom: return "bottom"
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            edge = self._edge_at(event.position().toPoint())
            if edge:
                self._resizing = True
                self._resize_edge = edge
                self._start_pos = event.globalPosition().toPoint()
                self._start_geo = self.geometry()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()

        if self._resizing:
            delta = event.globalPosition().toPoint() - self._start_pos
            geo = self._start_geo
            x, y, w, h = geo.x(), geo.y(), geo.width(), geo.height()

            if "left" in self._resize_edge:
                x += delta.x()
                w -= delta.x()
            if "right" in self._resize_edge:
                w += delta.x()
            if "top" in self._resize_edge:
                y += delta.y()
                h -= delta.y()
            if "bottom" in self._resize_edge:
                h += delta.y()

            w = max(w, self.minimumWidth())
            h = max(h, self.minimumHeight())
            self.setGeometry(x, y, w, h)
        else:
            edge = self._edge_at(pos)
            cursor_map = {
                "left": Qt.SizeHorCursor, "right": Qt.SizeHorCursor,
                "top": Qt.SizeVerCursor, "bottom": Qt.SizeVerCursor,
                "top_left": Qt.SizeFDiagCursor, "bottom_right": Qt.SizeFDiagCursor,
                "top_right": Qt.SizeBDiagCursor, "bottom_left": Qt.SizeBDiagCursor,
            }
            self.setCursor(cursor_map.get(edge, Qt.ArrowCursor))

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._resizing = False
        self._resize_edge = None
        super().mouseReleaseEvent(event)
