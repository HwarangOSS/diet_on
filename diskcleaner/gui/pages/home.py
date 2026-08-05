from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from diskcleaner.gui.components.power_button import PowerButton
from diskcleaner.gui.typo import body, play_large


class HomePage(QWidget):
    scan_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("homePage")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(0)

        self.power_button = PowerButton()
        layout.addWidget(self.power_button, alignment=Qt.AlignCenter)

        layout.addSpacing(20)

        self.click_label = QLabel("Click")
        self.click_label.setFont(play_large())
        self.click_label.setObjectName("clickLabel")
        self.click_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.click_label)

        layout.addSpacing(8)

        self.sub_label = QLabel("불필요한 파일을\n한번에 간편하게 정리해요")
        self.sub_label.setTextFormat(Qt.PlainText)
        self.sub_label.setFont(body())
        self.sub_label.setObjectName("subLabel")
        self.sub_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.sub_label)

        self.power_button.clicked_scan.connect(self.scan_requested.emit)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        canvas_size = min(self.width(), self.height())
        self.power_button.update_responsive_size(canvas_size)

    def refresh_fonts(self):
        self.click_label.setFont(play_large())
        self.sub_label.setFont(body())
