import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QLabel, QVBoxLayout, QWidget

from diskcleaner.gui.components.power_button import PowerButton
from diskcleaner.gui.typo import body_md, body_mini, headline

# 홈 디렉토리 전체는 느려서(파일 수가 많으면 분류/중복탐지가 오래 걸림) 테스트할 땐
# DIETON_SCAN_PATH 환경변수로 작은 폴더 하나만 지정해서 빠르게 돌릴 수 있게 함.
# 예 (PowerShell): $env:DIETON_SCAN_PATH = "C:\Users\mings\Downloads\test"
DEFAULT_SCAN_PATH = os.environ.get("DIETON_SCAN_PATH") or str(Path.home())


class HomePage(QWidget):
    """전원 버튼으로 스캔 시작, 라벨 클릭으로 스캔 대상 폴더 선택."""

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

        layout.addSpacing(8)

        self.path_label = QLabel(f"검사 폴더: {self.scan_path} (클릭해서 변경)")
        self.path_label.setFont(body_mini())
        self.path_label.setObjectName("scanPathLabel")
        self.path_label.setAlignment(Qt.AlignCenter)
        self.path_label.setCursor(Qt.PointingHandCursor)
        self.path_label.mousePressEvent = lambda event: self._choose_scan_path()
        layout.addWidget(self.path_label)

        self.power_button.clicked_scan.connect(self.scan_requested.emit)

    def _choose_scan_path(self):
        """폴더 선택 다이얼로그 띄우고, 고르면 scan_path/라벨 갱신."""
        chosen = QFileDialog.getExistingDirectory(self, "검사할 폴더 선택", self.scan_path)
        if chosen:
            self.scan_path = chosen
            self.path_label.setText(f"검사 폴더: {self.scan_path} (클릭해서 변경)")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        canvas_size = min(self.width(), self.height())
        self.power_button.update_responsive_size(canvas_size)

    def refresh_fonts(self):
        self.click_label.setFont(headline())
        self.sub_label.setFont(body_md())
        self.path_label.setFont(body_mini())

    def apply_theme(self, dark: bool):
        self.power_button.set_dark(dark)

    def get_scan_path(self) -> str:
        """스캔 대상 경로. 기본값은 홈 디렉토리(또는 DIETON_SCAN_PATH)이고,
        path_label 클릭으로 사용자가 고르면 그 값으로 바뀜."""
        return self.scan_path
