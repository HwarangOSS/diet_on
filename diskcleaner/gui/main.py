import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from diskcleaner.gui.main_window import MainWindow
from diskcleaner.gui.pages.home import HomePage
from diskcleaner.gui.components.titlebar import TitleBar
from diskcleaner.gui.theme import apply_theme
from diskcleaner.gui.settings import load_dark_mode, save_dark_mode

app = QApplication(sys.argv)

window = MainWindow()
window.setWindowTitle("DietOn")

root_layout = QVBoxLayout(window)
root_layout.setContentsMargins(0, 0, 0, 0)
root_layout.setSpacing(0)

# 커스텀 타이틀바
titlebar = TitleBar()
titlebar.minimize_requested.connect(window.showMinimized)
titlebar.close_requested.connect(window.close)
root_layout.addWidget(titlebar)

home = HomePage()
home.scan_requested.connect(lambda: print("[DEBUG] 스캔 요청됨!"))
root_layout.addWidget(home)

# 마지막 테마 불러오기
is_dark = load_dark_mode()
apply_theme(window, dark=is_dark)
titlebar.apply_icon_colors(dark=is_dark)

window.show()

# 종료 시 테마 저장
app.aboutToQuit.connect(lambda: save_dark_mode(is_dark))

sys.exit(app.exec())
