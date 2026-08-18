from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from diskcleaner.gui.theme import DARK, LIGHT
from diskcleaner.gui.typo import FontFamily, get_font

from . import styles


def _with_alpha(hex_color: str, alpha: int) -> QColor:
    color = QColor(hex_color)
    color.setAlpha(alpha)
    return color


def _name_font(scale: float):
    return get_font(FontFamily.PRETENDARD_MEDIUM, 11, role="naming", scale=scale)


def _path_font(scale: float):
    return get_font(FontFamily.PRETENDARD_REGULAR, 8, role="body_md", scale=scale)


def _size_font(scale: float):
    return get_font(FontFamily.PRETENDARD_REGULAR, 7, role="body_mini", scale=scale)


class FileListItem(QWidget):
    toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("fileListItem")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._is_dark = False
        self._is_selected = True
        self._press_inside = False
        self._reason = ""
        self._name = ""
        self._path = ""
        self._scale = 1.0

        layout = QVBoxLayout(self)

        self._top_row = top_row = QHBoxLayout()

        self.name_label = QLabel()
        self.name_label.setObjectName("fileItemName")
        top_row.addWidget(self.name_label)
        top_row.addStretch()

        self.size_label = QLabel()
        self.size_label.setObjectName("fileItemSize")
        top_row.addWidget(self.size_label, alignment=Qt.AlignTop)

        layout.addLayout(top_row)

        self.path_label = QLabel()
        self.path_label.setObjectName("fileItemPath")
        layout.addWidget(self.path_label)

        layout.addStretch()

        self.reason_label = QLabel()
        self.reason_label.setObjectName("fileItemReason")
        self.reason_label.hide()
        layout.addWidget(self.reason_label)

        self._refresh_style()
        self.update_responsive_size(styles.REFERENCE_WIDTH)

    # API
    def set_file(
        self,
        name: str,
        path: str,
        size_bytes: int,
        reason: str | None = None,
    ):
        self._name = name
        self._path = path
        self._refresh_name_text()
        self._refresh_path_text()
        self.size_label.setText(styles.format_file_size(size_bytes))

        self._reason = reason or ""
        if self._reason:
            self.setToolTip(self._reason)
            self._refresh_reason_text()
            self.reason_label.show()
        else:
            self.setToolTip("")
            self.reason_label.setText("")
            self.reason_label.hide()

    def _refresh_name_text(self):
        if not self._name:
            return
        metrics = QFontMetrics(self.name_label.font())
        padding_h = round(styles.REF_PADDING_H * self._scale)
        top_row_gap = round(styles.REF_TOP_ROW_GAP * self._scale)
        size_width = self.size_label.sizeHint().width()
        available_width = max(self.width() - 2 * padding_h - size_width - top_row_gap, 0)
        elided = metrics.elidedText(self._name, Qt.ElideMiddle, available_width)
        self.name_label.setText(elided)
        self.name_label.setToolTip(self._name)
        self.name_label.setMaximumWidth(available_width)

    def _refresh_path_text(self):
        if not self._path:
            return
        metrics = QFontMetrics(self.path_label.font())
        padding_h = round(styles.REF_PADDING_H * self._scale)
        available_width = max(self.width() - 2 * padding_h, 0)
        elided = metrics.elidedText(self._path, Qt.ElideMiddle, available_width)
        self.path_label.setText(elided)
        self.path_label.setToolTip(self._path)
        self.path_label.setMaximumWidth(available_width)

    def _refresh_reason_text(self):
        if not self._reason:
            return
        metrics = QFontMetrics(self.reason_label.font())
        padding_h = round(styles.REF_PADDING_H * self._scale)
        available_width = self.width() - 2 * padding_h
        elided = metrics.elidedText(
            f"AI 사유: {self._reason}", Qt.ElideRight, max(available_width, 0)
        )
        self.reason_label.setText(elided)

    def minimumSizeHint(self):
        return QSize(1, self.height())

    def sizeHint(self):
        return QSize(styles.REF_HEIGHT * 3, self.height())

    def refresh_fonts(self):
        self.update_responsive_size(self.width() or styles.REFERENCE_WIDTH)

    def is_selected(self) -> bool:
        return self._is_selected

    def set_selected(self, selected: bool, emit: bool = False):
        if self._is_selected == selected:
            return
        self._is_selected = selected
        self._refresh_style()
        self.update()
        if emit:
            self.toggled.emit(self._is_selected)

    def set_dark(self, dark: bool):
        self._is_dark = dark
        self._refresh_style()
        self.update()

    def update_responsive_size(self, container_width: int):
        scale = container_width / styles.REFERENCE_WIDTH
        self._scale = scale

        self.name_label.setFont(_name_font(scale))
        self.path_label.setFont(_path_font(scale))
        self.size_label.setFont(_size_font(scale))
        self.reason_label.setFont(_size_font(scale))

        self.setFixedHeight(max(1, round(styles.REF_HEIGHT * scale)))

        h_margin = round(styles.REF_PADDING_H * scale)
        v_margin = round(styles.REF_PADDING_V * scale)
        self.layout().setContentsMargins(h_margin, v_margin, h_margin, v_margin)
        self.layout().setSpacing(round(styles.REF_ROW_GAP * scale))
        self._top_row.setSpacing(round(styles.REF_TOP_ROW_GAP * scale))
        self._refresh_name_text()
        self._refresh_path_text()
        self._refresh_reason_text()
        self.update()

    # 이벤트
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_name_text()
        self._refresh_path_text()
        self._refresh_reason_text()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_inside = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._press_inside:
            if self.rect().contains(event.position().toPoint()):
                self.set_selected(not self._is_selected, emit=True)
        self._press_inside = False
        super().mouseReleaseEvent(event)

    # 내부
    def _background_color(self) -> QColor:
        if self._is_dark:
            return QColor(LIGHT.primary) if self._is_selected else QColor(DARK.bg)
        if self._is_selected:
            return _with_alpha(LIGHT.primary, round(0.30 * 255))
        return QColor(LIGHT.bg)

    def _text_color(self) -> str:
        return "#FFFFFF" if self._is_dark else LIGHT.text_primary

    def _reason_color(self) -> str:
        return DARK.text_tertiary if self._is_dark else LIGHT.text_tertiary

    def _refresh_style(self):
        color = self._text_color()
        reason_color = self._reason_color()
        self.setStyleSheet(
            "QLabel#fileItemName, QLabel#fileItemPath, QLabel#fileItemSize {"
            f" color: {color}; background: transparent; }}"
            "QLabel#fileItemReason {"
            f" color: {reason_color}; background: transparent; }}"
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        radius = round(styles.REF_CORNER_RADIUS * self._scale)

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), radius, radius)
        painter.setClipPath(path)

        painter.fillPath(path, self._background_color())

        glow = QColor(styles.SELECT_SHADOW_COLOR)
        layers = 5
        max_width = round(styles.REF_GLOW_SPREAD * self._scale) * 2
        for i in range(layers):
            t = i / (layers - 1)
            pen_width = max(1, round(max_width * (1 - t)))
            alpha = int(70 * (1 - t))
            pen = QPen(QColor(glow.red(), glow.green(), glow.blue(), alpha))
            pen.setWidthF(pen_width)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

        painter.end()
