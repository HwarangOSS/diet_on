import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QFileDialog, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from diskcleaner.gui.components.power_button import PowerButton
from diskcleaner.gui.theme import palette_for
from diskcleaner.gui.typo import body_md, headline, path_quote, rem

DEFAULT_SCAN_PATH = os.environ.get("DIETON_SCAN_PATH") or str(Path.home())

SUB_TEXT = "안의 불필요한 파일을\n한번에 간편하게 정리해요"

# rem 단위(1rem=16px)
POWER_BUTTON_GAP_REM = 20 / 16
CLICK_GAP_REM = 8 / 16
SUB_GAP_REM = 8 / 16
BUTTON_TOP_GAP_REM = 16 / 16
BUTTON_RADIUS_REM = 18 / 16
BUTTON_PADDING_V_REM = 10 / 16
BUTTON_PADDING_H_REM = 28 / 16


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

        self.change_path_button = QPushButton("탐색 파일 변경")
        self.change_path_button.setObjectName("changePathButton")
        self.change_path_button.setFont(body_md())
        self.change_path_button.setCursor(Qt.PointingHandCursor)
        self.change_path_button.clicked.connect(self._choose_scan_path)
        layout.addWidget(self.change_path_button, alignment=Qt.AlignCenter)

        self.power_button.clicked_scan.connect(self.scan_requested.emit)

        self._refresh_path_quote_text()
        self._apply_responsive_size()

    def _choose_scan_path(self):
        """폴더 선택 다이얼로그 띄우고, 고르면 scan_path/라벨 갱신."""
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
        p = palette_for(self._is_dark)
        radius = rem(BUTTON_RADIUS_REM)
        padding_v = rem(BUTTON_PADDING_V_REM)
        padding_h = rem(BUTTON_PADDING_H_REM)
        self.change_path_button.setStyleSheet(f"""
            QPushButton#changePathButton {{
                background-color: {p.primary};
                color: #FFFFFF;
                border: none;
                border-radius: {radius}px;
                padding: {padding_v}px {padding_h}px;
            }}
            QPushButton#changePathButton:hover {{
                background-color: {p.primary_hover};
            }}
            QPushButton#changePathButton:pressed {{
                background-color: {p.primary_hover};
            }}
            """)

    def _apply_responsive_size(self):
        self._power_button_gap.changeSize(
            0, rem(POWER_BUTTON_GAP_REM), QSizePolicy.Minimum, QSizePolicy.Fixed
        )
        self._click_gap.changeSize(0, rem(CLICK_GAP_REM), QSizePolicy.Minimum, QSizePolicy.Fixed)
        self._sub_gap.changeSize(0, rem(SUB_GAP_REM), QSizePolicy.Minimum, QSizePolicy.Fixed)
        self._button_top_gap.changeSize(
            0, rem(BUTTON_TOP_GAP_REM), QSizePolicy.Minimum, QSizePolicy.Fixed
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
        self._apply_button_style()

    def get_scan_path(self) -> str:
        """스캔 대상 경로. 기본값은 홈 디렉토리(또는 DIETON_SCAN_PATH)이고,
        버튼 클릭으로 사용자가 고르면 그 값으로 바뀜."""
        return self.scan_path
