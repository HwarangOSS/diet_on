import os
from pathlib import Path

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFileDialog, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from diskcleaner.gui.components.power_button import PowerButton
from diskcleaner.gui.theme import palette_for
from diskcleaner.gui.typo import body_md, headline, path_quote, rem

from . import styles

DEFAULT_SCAN_PATH = os.environ.get("DIETON_SCAN_PATH") or str(Path.home())

SUB_TEXT = "안의 불필요한 파일을\n한번에 간편하게 정리해요"


class ChangePathButton(QPushButton):
    """Qt 스타일시트는 inset box-shadow를 지원하지 않아 직접 그려서 구현한 버튼."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._is_dark = False

    def set_dark(self, dark: bool):
        self._is_dark = dark
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = rect.height() / 2

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        # 다크 모드에서는 PowerButton과 동일하게 palette의 primary 색을 사용
        p = palette_for(self._is_dark)
        fill = p.primary_hover if (self.underMouse() or self.isDown()) else p.primary
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(fill))
        painter.drawPath(path)

        painter.setClipPath(path)
        self._paint_inset_glow(painter, rect, radius)
        painter.setClipping(False)

        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(self.font())
        painter.drawText(rect, Qt.AlignCenter, self.text())
        painter.end()

    def _paint_inset_glow(self, painter: QPainter, rect: QRectF, radius: float):
        blur_radius = styles.BUTTON_GLOW_BLUR_RADIUS
        steps = max(1, round(blur_radius))
        for i in range(steps):
            inset = i + 0.5
            alpha = round(styles.BUTTON_GLOW_MAX_ALPHA * (1 - i / steps) ** 2)
            pen = QPen(QColor(255, 255, 255, alpha))
            pen.setWidthF(1.4)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            inner_rect = rect.adjusted(inset, inset, -inset, -inset)
            inner_radius = max(radius - inset, 0.0)
            painter.drawRoundedRect(inner_rect, inner_radius, inner_radius)

    def enterEvent(self, event):
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.update()


class HomePage(QWidget):
    scan_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("homePage")

        self.scan_path = DEFAULT_SCAN_PATH
        self._is_dark = False

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(0)

        self.power_button = PowerButton()
        layout.addWidget(self.power_button, alignment=Qt.AlignCenter)

        layout.addSpacing(0)
        self._power_button_gap = layout.itemAt(layout.count() - 1).spacerItem()

        self.click_label = QLabel("Click")
        self.click_label.setFont(headline())
        self.click_label.setObjectName("clickLabel")
        self.click_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.click_label)

        layout.addSpacing(0)
        self._click_gap = layout.itemAt(layout.count() - 1).spacerItem()

        self.path_quote_label = QLabel()
        self.path_quote_label.setFont(path_quote())
        self.path_quote_label.setObjectName("pathQuoteLabel")
        self.path_quote_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.path_quote_label)

        layout.addSpacing(0)
        self._sub_gap = layout.itemAt(layout.count() - 1).spacerItem()

        self.sub_label = QLabel(SUB_TEXT)
        self.sub_label.setTextFormat(Qt.PlainText)
        self.sub_label.setFont(body_md())
        self.sub_label.setObjectName("subLabel")
        self.sub_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.sub_label)

        layout.addSpacing(0)
        self._button_top_gap = layout.itemAt(layout.count() - 1).spacerItem()

        self.change_path_button = ChangePathButton("탐색 파일 변경")
        self.change_path_button.setObjectName("changePathButton")
        self.change_path_button.setFont(body_md())
        self.change_path_button.setCursor(Qt.PointingHandCursor)
        self.change_path_button.clicked.connect(self._choose_scan_path)
        layout.addWidget(self.change_path_button, alignment=Qt.AlignCenter)

        self.power_button.clicked_scan.connect(self.scan_requested.emit)

        self._refresh_path_quote_text()
        self._apply_responsive_size()

    def _choose_scan_path(self):
        chosen = QFileDialog.getExistingDirectory(self, "검사할 폴더 선택", self.scan_path)
        if chosen:
            self.scan_path = chosen
            self._refresh_path_quote_text()

    def _refresh_path_quote_text(self):
        metrics = QFontMetrics(self.path_quote_label.font())
        available_width = max(self.width() - 40, 120)
        elided = metrics.elidedText(self.scan_path, Qt.ElideMiddle, available_width)
        self.path_quote_label.setText(f'"{elided}"')
        self.path_quote_label.setToolTip(self.scan_path)

    def _apply_button_style(self):
        self.change_path_button.setFixedSize(
            rem(styles.BUTTON_WIDTH_REM), rem(styles.BUTTON_HEIGHT_REM)
        )

    def _apply_responsive_size(self):
        self._power_button_gap.changeSize(
            0, rem(styles.POWER_BUTTON_GAP_REM), QSizePolicy.Minimum, QSizePolicy.Fixed
        )
        self._click_gap.changeSize(
            0, rem(styles.CLICK_GAP_REM), QSizePolicy.Minimum, QSizePolicy.Fixed
        )
        self._sub_gap.changeSize(0, rem(styles.SUB_GAP_REM), QSizePolicy.Minimum, QSizePolicy.Fixed)
        self._button_top_gap.changeSize(
            0, rem(styles.BUTTON_TOP_GAP_REM), QSizePolicy.Minimum, QSizePolicy.Fixed
        )
        self.layout().invalidate()
        self._apply_button_style()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        canvas_size = min(self.width(), self.height())
        self.power_button.update_responsive_size(canvas_size)
        self._refresh_path_quote_text()

    def refresh_fonts(self):
        self.click_label.setFont(headline())
        self.path_quote_label.setFont(path_quote())
        self.sub_label.setFont(body_md())
        self.change_path_button.setFont(body_md())
        self._apply_responsive_size()
        self._refresh_path_quote_text()

    def apply_theme(self, dark: bool):
        self._is_dark = dark
        self.power_button.set_dark(dark)
        self.change_path_button.set_dark(dark)
        self._apply_button_style()

    def get_scan_path(self) -> str:
        return self.scan_path
