import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from diskcleaner.gui.components.power_button import PowerButton
from diskcleaner.gui.typo import body_md, headline

# 폴더 선택 UI가 아직 없어서 우선 홈 디렉토리를 기본 스캔 대상으로 둔다.
# 홈 디렉토리 전체는 느려서(파일 수가 많으면 분류/중복탐지가 오래 걸림) 테스트할 땐
# DIETON_SCAN_PATH 환경변수로 작은 폴더 하나만 지정해서 빠르게 돌릴 수 있게 함.
# 예 (PowerShell): $env:DIETON_SCAN_PATH = "C:\Users\mings\Downloads\test"
# 폴더 선택 기능이 생기면 get_scan_path()가 사용자가 고른 경로를 반환하도록
# 이 자리만 바꾸면 됨 (호출부인 main.py는 그대로).
DEFAULT_SCAN_PATH = os.environ.get("DIETON_SCAN_PATH") or str(Path.home())


class HomePage(QWidget):
    scan_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("homePage")

        self.scan_path = DEFAULT_SCAN_PATH

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(0)

        self.power_button = PowerButton()
        layout.addWidget(self.power_button, alignment=Qt.AlignCenter)

        layout.addSpacing(20)

        self.click_label = QLabel("Click")
        self.click_label.setFont(headline())
        self.click_label.setObjectName("clickLabel")
        self.click_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.click_label)

        layout.addSpacing(8)

        self.sub_label = QLabel("불필요한 파일을\n한번에 간편하게 정리해요")
        self.sub_label.setTextFormat(Qt.PlainText)
        self.sub_label.setFont(body_md())
        self.sub_label.setObjectName("subLabel")
        self.sub_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.sub_label)

        self.power_button.clicked_scan.connect(self.scan_requested.emit)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        canvas_size = min(self.width(), self.height())
        self.power_button.update_responsive_size(canvas_size)

    def refresh_fonts(self):
        self.click_label.setFont(headline())
        self.sub_label.setFont(body_md())

    def apply_theme(self, dark: bool):
        self.power_button.set_dark(dark)

    def get_scan_path(self) -> str:
        """스캔 대상 경로. 지금은 홈 디렉토리 고정값이고, 폴더 선택 UI가
        생기면 self.scan_path를 그때 고른 값으로 바꿔주면 됨."""
        return self.scan_path
