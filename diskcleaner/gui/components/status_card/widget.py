from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QSizePolicy, QWidget

from diskcleaner.gui.theme import LIGHT, palette_for
from diskcleaner.gui.typo import FontFamily, get_font

from . import icons, styles

REFERENCE_WIDTH = 880  # result.py의 REFERENCE_WIDTH와 반드시 같아야 카드 크기가 일관됨


def _message_font(scale: float):
    return get_font(FontFamily.PRETENDARD_REGULAR, 13, role="body_md", scale=scale)


def _meta_font(scale: float):
    return get_font(FontFamily.PRETENDARD_REGULAR, 11, role="body_mini", scale=scale)


class StatusCard(QWidget):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusCard")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._is_dark = False
        self._status = styles.STATUS_SUCCESS
        self._press_inside = False
        self._scale = 1.0

        self._glow_effect = QGraphicsDropShadowEffect(self)
        self._glow_effect.setOffset(0, 0)
        self._glow_effect.setEnabled(False)
        self.setGraphicsEffect(self._glow_effect)

        layout = QHBoxLayout(self)

        self.icon_label = QLabel()
        layout.addWidget(self.icon_label, alignment=Qt.AlignVCenter)

        self.message_label = QLabel()
        self.message_label.setObjectName("statusMessage")
        layout.addWidget(self.message_label, 1, alignment=Qt.AlignVCenter)

        layout.addSpacing(0)
        self._meta_gap_spacer = layout.itemAt(layout.count() - 1).spacerItem()

        self.meta_label = QLabel()
        self.meta_label.setObjectName("statusMeta")
        self.meta_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.meta_label, alignment=Qt.AlignVCenter)

        self._apply_icon()
        self._refresh_text_colors()
        self.update_responsive_size(REFERENCE_WIDTH)

    # API
    def set_result(self, status: str, message: str, count: int, size_bytes: int):
        self._status = status
        self.message_label.setText(message)
        self.meta_label.setText(f"{count}개 ({styles.format_gb(size_bytes)})")
        self._apply_icon()
        self.update()

    def refresh_fonts(self):
        """전역 폰트 스케일 변경 시 카드 내부 라벨도 함께 갱신."""
        self.message_label.setFont(_message_font(self._scale))
        self.meta_label.setFont(_meta_font(self._scale))

    def set_dark(self, dark: bool):
        self._is_dark = dark
        self._apply_icon()
        self._refresh_text_colors()

        self._glow_effect.setEnabled(dark)
        if dark:
            self._glow_effect.setColor(QColor(255, 255, 255, 64))
            self._glow_effect.setBlurRadius(round(styles.REF_GLOW_BLUR_RADIUS * self._scale))
        self.update()

    def update_responsive_size(self, container_width: int):
        scale = container_width / REFERENCE_WIDTH
        self._scale = scale

        self.message_label.setFont(_message_font(scale))
        self.meta_label.setFont(_meta_font(scale))

        self.setFixedHeight(max(1, round(styles.REF_CARD_HEIGHT * scale)))

        margin = round(styles.REF_PADDING * scale)
        self.layout().setContentsMargins(margin, margin, margin, margin)
        self.layout().setSpacing(round(styles.REF_ICON_GAP * scale))
        self._meta_gap_spacer.changeSize(
            round(styles.REF_META_GAP * scale), 0, QSizePolicy.Fixed, QSizePolicy.Minimum
        )
        self.layout().invalidate()

        icon_size = max(1, round(styles.REF_ICON_SIZE * scale))
        self.icon_label.setFixedSize(icon_size, icon_size)
        self._apply_icon(icon_size)

        if self._is_dark:
            self._glow_effect.setBlurRadius(round(styles.REF_GLOW_BLUR_RADIUS * scale))

        self.update()

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
        size = icon_size or self.icon_label.width() or round(styles.REF_ICON_SIZE * self._scale)
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

    def _refresh_text_colors(self):
        p = palette_for(self._is_dark)
        self.setStyleSheet(
            f"""
            QLabel#statusMessage {{ color: {p.text_primary}; background: transparent; }}
            QLabel#statusMeta {{ color: {p.text_secondary}; background: transparent; }}
        """
        )

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
        layers = 3
        max_width = round(styles.REF_GLOW_SPREAD * self._scale) * 2
        for i in range(layers):
            t = i / (layers - 1)
            # t=0(가장 두꺼운 번짐)은 옅게, t=1(가장 얇은 선)은 또렷하게 그려서
            # 흐릿한 덩어리가 아니라 얇고 선명한 테두리 + 은은한 번짐으로 보이게 함.
            pen_width = max(1, round(max_width * (1 - t)))
            alpha = int(150 * t)
            pen = QPen(QColor(glow.red(), glow.green(), glow.blue(), alpha))
            pen.setWidthF(pen_width)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

        painter.end()
