from dotenv import load_dotenv

load_dotenv()

import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QStackedWidget, QVBoxLayout

from diskcleaner.core.llm_advisor import test_connection
from diskcleaner.gui.components.titlebar import TitleBar
from diskcleaner.gui.main_window import MainWindow
from diskcleaner.gui.pages.home import HomePage
from diskcleaner.gui.pages.loading import LoadingPage
from diskcleaner.gui.settings import load_dark_mode, save_dark_mode
from diskcleaner.gui.theme import apply_theme
from diskcleaner.gui.typo import set_global_scale

app = QApplication(sys.argv)

window = MainWindow()
window.setWindowTitle("DietOn")

root_layout = QVBoxLayout(window)
root_layout.setContentsMargins(0, 0, 0, 0)
root_layout.setSpacing(0)

titlebar = TitleBar()
titlebar.minimize_requested.connect(window.showMinimized)
titlebar.close_requested.connect(window.close)
root_layout.addWidget(titlebar)

stack = QStackedWidget()

home = HomePage()
loading = LoadingPage()

stack.addWidget(home)
stack.addWidget(loading)

root_layout.addWidget(stack)


def go_to_loading():
    stack.setCurrentWidget(loading)
    loading.start()
    print("[DEBUG] 스캔 요청됨! (로딩 페이지로 전환)")

    try:
        result = test_connection()
        print(f"[DEBUG] LLM 응답: {result}")
    except Exception as e:
        print(f"[ERROR] API 연결 실패: {e}")

    # 임시: 프로그레스바 테스트
    fake_progress = {"value": 0}

    def fake_tick():
        fake_progress["value"] += 5
        loading.update_progress(fake_progress["value"])
        print(f"[DEBUG] 진행률: {fake_progress['value']}%")
        if fake_progress["value"] >= 100:
            fake_timer.stop()

    fake_timer = QTimer()
    fake_timer.timeout.connect(fake_tick)
    fake_timer.start(150)
    go_to_loading._fake_timer = fake_timer


#####################

home.scan_requested.connect(go_to_loading)


def toggle_theme():
    global is_dark
    is_dark = not is_dark
    apply_theme(window, dark=is_dark)
    titlebar.apply_icon_colors(dark=is_dark)
    loading.apply_theme(dark=is_dark)
    save_dark_mode(is_dark)


titlebar.menu_requested.connect(toggle_theme)

is_dark = load_dark_mode()
apply_theme(window, dark=is_dark)
titlebar.apply_icon_colors(dark=is_dark)
loading.apply_theme(dark=is_dark)

# 폰트 연결
set_global_scale(window.width())
window.font_scale_changed.connect(home.refresh_fonts)
window.font_scale_changed.connect(loading.refresh_fonts)
window.font_scale_changed.connect(titlebar.refresh_fonts)
home.refresh_fonts()
loading.refresh_fonts()
titlebar.refresh_fonts()

window.show()

app.aboutToQuit.connect(lambda: save_dark_mode(is_dark))

sys.exit(app.exec())
