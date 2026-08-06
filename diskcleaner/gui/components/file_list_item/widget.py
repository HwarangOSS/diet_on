from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from diskcleaner.gui.theme import DARK, LIGHT
from diskcleaner.gui.typo import BASE_WINDOW_WIDTH, body_md, body_mini, hashtag, naming

from . import styles


def _with_alpha(hex_color: str, alpha: int) -> QColor:
    color = QColor(hex_color)
    color.setAlpha(alpha)
    return color


class FileListItem(QWidget):
    toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("fileListItem")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.PointingHandCursor)

        self._is_dark = False
        self._is_selected = True
        self._scale = 1.0
        self._press_inside = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            styles.BASE_PADDING_H,
            styles.BASE_PADDING_V,
            styles.BASE_PADDING_H,
            styles.BASE_PADDING_V,
        )
        layout.setSpacing(styles.BASE_ROW_GAP)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.name_label = QLabel()
        self.name_label.setObjectName("fileItemName")
        self.name_label.setFont(naming())
        top_row.addWidget(self.name_label)
        top_row.addStretch()

        self.size_label = QLabel()
        self.size_label.setObjectName("fileItemSize")
        self.size_label.setFont(body_mini())
        top_row.addWidget(self.size_label, alignment=Qt.AlignTop)

        layout.addLayout(top_row)

        self.path_label = QLabel()
        self.path_label.setObjectName("fileItemPath")
        self.path_label.setFont(body_md())
        layout.addWidget(self.path_label)

        layout.addStretch()

        bottom_row = QHBoxLayout()
        bottom_row.addStretch()

        self.hashtag_label = QLabel()
        self.hashtag_label.setObjectName("fileItemHashtag")
        self.hashtag_label.setFont(hashtag())
        bottom_row.addWidget(self.hashtag_label)

        layout.addLayout(bottom_row)

        self.setFixedSize(styles.BASE_WIDTH, styles.BASE_HEIGHT)
        self._refresh_style()

    # API
    def set_file(self, name: str, path: str, size_bytes: int, hashtags: list[str] | None = None):
        self.name_label.setText(name)
        self.path_label.setText(path)
        self.size_label.setText(styles.format_file_size(size_bytes))

        tags = hashtags or []
        if tags:
            self.hashtag_label.setText(" ".join(t if t.startswith("#") else f"#{t}" for t in tags))
            self.hashtag_label.show()
        else:
            self.hashtag_label.setText("")
            self.hashtag_label.hide()

    def set_hashtag_visible(self, visible: bool):
        self.hashtag_label.setVisible(visible)

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
        scale = container_width / BASE_WINDOW_WIDTH
        scale = max(styles.SCALE_MIN, min(scale, styles.SCALE_MAX))
        self._scale = scale

        self.setFixedSize(round(styles.BASE_WIDTH * scale), round(styles.BASE_HEIGHT * scale))

        h_margin = round(styles.BASE_PADDING_H * scale)
        v_margin = round(styles.BASE_PADDING_V * scale)
        self.layout().setContentsMargins(h_margin, v_margin, h_margin, v_margin)
        self.layout().setSpacing(round(styles.BASE_ROW_GAP * scale))
        self.update()

    # 이벤트
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

    def _refresh_style(self):
        color = self._text_color()
        self.setStyleSheet(
            "QLabel#fileItemName, QLabel#fileItemPath, "
            "QLabel#fileItemHashtag, QLabel#fileItemSize {"
            f" color: {color}; background: transparent; }}"
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        radius = styles.CORNER_RADIUS * self._scale

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), radius, radius)
        painter.setClipPath(path)

        painter.fillPath(path, self._background_color())

        glow = QColor(styles.SELECT_SHADOW_COLOR)
        layers = 5
        max_width = styles.GLOW_SPREAD * 2 * self._scale
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
