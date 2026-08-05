# 화면 레이아웃
from PySide6.QtCore import QEvent, QPoint, Qt, Signal
from PySide6.QtWidgets import QApplication, QWidget

from diskcleaner.gui.typo import set_global_scale

BORDER_WIDTH = 6

CURSOR_MAP = {
    "left": Qt.SizeHorCursor,
    "right": Qt.SizeHorCursor,
    "top": Qt.SizeVerCursor,
    "bottom": Qt.SizeVerCursor,
    "top_left": Qt.SizeFDiagCursor,
    "bottom_right": Qt.SizeFDiagCursor,
    "top_right": Qt.SizeBDiagCursor,
    "bottom_left": Qt.SizeBDiagCursor,
}


class MainWindow(QWidget):
    font_scale_changed = Signal()

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
        self._cursor_overridden = False  # --- 추가 ---

    def _enable_edge_resize_for(self, widget: QWidget):
        widget.setMouseTracking(True)
        widget.installEventFilter(self)
        for child in widget.findChildren(QWidget):
            child.setMouseTracking(True)
            child.installEventFilter(self)

    def showEvent(self, event):
        super().showEvent(event)
        self._enable_edge_resize_for(self)

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.MouseMove, QEvent.MouseButtonPress, QEvent.MouseButtonRelease):
            if hasattr(event, "globalPosition"):
                global_pos = event.globalPosition().toPoint()
                local_pos = self.mapFromGlobal(global_pos)

                if event.type() == QEvent.MouseMove:
                    self._handle_move(local_pos, event)
                elif event.type() == QEvent.MouseButtonPress:
                    if self._handle_press(local_pos, event):
                        return True
                elif event.type() == QEvent.MouseButtonRelease:
                    self._handle_release()

        return super().eventFilter(obj, event)

    def _edge_at(self, pos: QPoint) -> str | None:
        rect = self.rect()
        left = pos.x() <= BORDER_WIDTH
        right = pos.x() >= rect.width() - BORDER_WIDTH
        top = pos.y() <= BORDER_WIDTH
        bottom = pos.y() >= rect.height() - BORDER_WIDTH

        if top and left:
            return "top_left"
        if top and right:
            return "top_right"
        if bottom and left:
            return "bottom_left"
        if bottom and right:
            return "bottom_right"
        if left:
            return "left"
        if right:
            return "right"
        if top:
            return "top"
        if bottom:
            return "bottom"
        return None

    def _handle_press(self, local_pos: QPoint, event) -> bool:
        edge = self._edge_at(local_pos)
        if edge:
            self._resizing = True
            self._resize_edge = edge
            self._start_pos = event.globalPosition().toPoint()
            self._start_geo = self.geometry()
            return True
        return False

    def _handle_move(self, local_pos: QPoint, event):
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
            edge = self._edge_at(local_pos)
            self._apply_edge_cursor(edge)

    def _apply_edge_cursor(self, edge: str | None):
        if edge:
            cursor = CURSOR_MAP.get(edge, Qt.ArrowCursor)
            if self._cursor_overridden:
                QApplication.changeOverrideCursor(cursor)
            else:
                QApplication.setOverrideCursor(cursor)
                self._cursor_overridden = True
        else:
            if self._cursor_overridden:
                QApplication.restoreOverrideCursor()
                self._cursor_overridden = False

    def _handle_release(self):
        was_resizing = self._resizing
        self._resizing = False
        self._resize_edge = None

        if was_resizing:
            set_global_scale(self.width())
            self.font_scale_changed.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._resizing:
            set_global_scale(self.width())
            self.font_scale_changed.emit()
