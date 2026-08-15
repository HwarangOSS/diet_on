from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QSizePolicy, QWidget

from diskcleaner.gui.theme import LIGHT, palette_for
from diskcleaner.gui.typo import body_md, body_mini, rem, set_global_scale

from . import icons, styles


class StatusCard(QWidget):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusCard")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.PointingHandCursor)

        self._is_dark = False
        self._status = styles.STATUS_SUCCESS
        self._press_inside = False

        self._glow_effect = QGraphicsDropShadowEffect(self)
        self._glow_effect.setOffset(0, 0)
        self._glow_effect.setEnabled(False)
        self.setGraphicsEffect(self._glow_effect)

        layout = QHBoxLayout(self)
        padding = rem(styles.PADDING_REM)
        layout.setContentsMargins(padding, padding, padding, padding)
        layout.setSpacing(rem(styles.ICON_GAP_REM))

        self.icon_label = QLabel()
        icon_size = rem(styles.ICON_SIZE_REM)
        self.icon_label.setFixedSize(icon_size, icon_size)
        layout.addWidget(self.icon_label, alignment=Qt.AlignVCenter)

        self.message_label = QLabel()
        self.message_label.setObjectName("statusMessage")
        self.message_label.setFont(body_md())
        layout.addWidget(self.message_label, 1, alignment=Qt.AlignVCenter)

        layout.addSpacing(rem(styles.META_GAP_REM))
        self._meta_gap_spacer = layout.itemAt(layout.count() - 1).spacerItem()

        self.meta_label = QLabel()
        self.meta_label.setObjectName("statusMeta")
        self.meta_label.setFont(body_mini())
        self.meta_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.meta_label, alignment=Qt.AlignVCenter)

        self.setFixedSize(rem(styles.CARD_WIDTH_REM), rem(styles.CARD_HEIGHT_REM))
        self._apply_icon()

    # API
    def set_result(self, status: str, message: str, count: int, size_bytes: int):
        self._status = status
        self.message_label.setText(message)
        self.meta_label.setText(f"{count}개 ({styles.format_gb(size_bytes)})")
        self._apply_icon()
        self.update()

    def refresh_fonts(self):
        """전역 폰트 스케일 변경 시 카드 내부 라벨도 함께 갱신."""
        self.message_label.setFont(body_md())
        self.meta_label.setFont(body_mini())

    def set_dark(self, dark: bool):
        self._is_dark = dark
        self._apply_icon()

        self._glow_effect.setEnabled(dark)
        if dark:
            self._glow_effect.setColor(QColor(255, 255, 255, 64))
            self._glow_effect.setBlurRadius(rem(styles.GLOW_BLUR_RADIUS_REM))
        self.update()

    def update_responsive_size(self, container_width: int):
        set_global_scale(container_width)

        self.setFixedSize(rem(styles.CARD_WIDTH_REM), rem(styles.CARD_HEIGHT_REM))

        margin = rem(styles.PADDING_REM)
        self.layout().setContentsMargins(margin, margin, margin, margin)
        self.layout().setSpacing(rem(styles.ICON_GAP_REM))
        self._meta_gap_spacer.changeSize(
            rem(styles.META_GAP_REM), 0, QSizePolicy.Fixed, QSizePolicy.Minimum
        )
        self.layout().invalidate()

        icon_size = rem(styles.ICON_SIZE_REM)
        self.icon_label.setFixedSize(icon_size, icon_size)
        self._apply_icon(icon_size)

        if self._is_dark:
            self._glow_effect.setBlurRadius(rem(styles.GLOW_BLUR_RADIUS_REM))

    # 이벤트
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_inside = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._press_inside:
            if self.rect().contains(event.position().toPoint()):
                self.clicked.emit()
        self._press_inside = False
        super().mouseReleaseEvent(event)

    # 내부
    def _apply_icon(self, icon_size: int | None = None):
        size = icon_size or self.icon_label.width() or rem(styles.ICON_SIZE_REM)
        p = palette_for(self._is_dark)
        color = p.danger if self._status == styles.STATUS_DANGER else p.success
        maker = (
            icons.make_warning_icon
            if self._status == styles.STATUS_DANGER
            else icons.make_check_icon
        )
        self.icon_label.setPixmap(maker(color, size=size))

    def _glow_color(self) -> str:
        return LIGHT.danger if self._status == styles.STATUS_DANGER else LIGHT.success

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        radius = h * styles.CORNER_RADIUS_RATIO

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), radius, radius)
        painter.setClipPath(path)

        p = palette_for(self._is_dark)
        painter.fillPath(path, QColor(p.bg))
        glow = QColor(self._glow_color())
        layers = 6
        max_width = rem(styles.GLOW_SPREAD_REM) * 2
        for i in range(layers):
            t = i / (layers - 1)
            pen_width = max(1, round(max_width * (1 - t)))
            alpha = int(90 * (1 - t))
            pen = QPen(QColor(glow.red(), glow.green(), glow.blue(), alpha))
            pen.setWidthF(pen_width)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

        painter.end()
