from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from diskcleaner.gui.typo import play_large, body
from diskcleaner.gui.components.power_button import PowerButton

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

        # Click
        click_label = QLabel("Click")
        click_label.setFont(play_large())
        click_label.setObjectName("clickLabel")
        click_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(click_label)

        layout.addSpacing(8)

        # 설명
        sub_label = QLabel("불필요한 파일을\n한번에 간편하게 정리해요")
        sub_label.setTextFormat(Qt.PlainText) 
        sub_label.setFont(body())
        sub_label.setObjectName("subLabel")
        sub_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub_label)

        self.power_button.clicked_scan.connect(self.scan_requested.emit)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        canvas_size = min(self.width(), self.height())
        self.power_button.update_responsive_size(canvas_size)
