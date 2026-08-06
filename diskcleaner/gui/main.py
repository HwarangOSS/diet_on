import sys

from dotenv import load_dotenv
from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication, QStackedWidget, QVBoxLayout

from diskcleaner.gui.analysis_worker import start_analysis
from diskcleaner.gui.components.titlebar import TitleBar
from diskcleaner.gui.main_window import MainWindow
from diskcleaner.gui.pages.delete_detail import DeletePage
from diskcleaner.gui.pages.duplicate_detail import DuplicatePage
from diskcleaner.gui.pages.home import HomePage
from diskcleaner.gui.pages.loading import LoadingPage
from diskcleaner.gui.pages.result import CATEGORY_DELETE_TARGET, CATEGORY_DUPLICATE, ResultPage
from diskcleaner.gui.result_mapping import (
    report_to_delete_files,
    report_to_duplicate_groups,
    report_to_results,
)
from diskcleaner.gui.settings import load_dark_mode, save_dark_mode
from diskcleaner.gui.theme import apply_theme
from diskcleaner.gui.typo import set_global_scale

PROGRESS_TICK_MS = 200
PROGRESS_TICK_STEP = 3
PROGRESS_TICK_CAP = 90


class _AnalysisBridge(QObject):
    def __init__(self, on_finished, on_error):
        super().__init__()
        self._on_finished = on_finished
        self._on_error = on_error

    def handle_finished(self, report):
        self._on_finished(report)

    def handle_error(self, message):
        self._on_error(message)


def main():
    load_dotenv()

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
    result = ResultPage()
    delete_detail = DeletePage()
    duplicate_detail = DuplicatePage()

    stack.addWidget(home)
    stack.addWidget(loading)
    stack.addWidget(result)
    stack.addWidget(delete_detail)
    stack.addWidget(duplicate_detail)

    root_layout.addWidget(stack)

    state = {
        "thread": None,
        "worker": None,
        "bridge": None,
        "progress_timer": None,
        "progress_value": 0,
        "report": None,
    }

    def _stop_progress_timer():
        timer = state["progress_timer"]
        if timer is not None:
            timer.stop()
            state["progress_timer"] = None

    def _wait_for_thread():
        thread = state["thread"]
        if thread is not None:
            thread.wait()

    def _tick_progress():
        if state["progress_value"] < PROGRESS_TICK_CAP:
            state["progress_value"] += PROGRESS_TICK_STEP
            loading.update_progress(state["progress_value"])
            print(f"[진행] {state['progress_value']}% (스캔 백그라운드 진행 중)")

    def on_analysis_finished(report):
        _stop_progress_timer()
        _wait_for_thread()
        loading.update_progress(100)
        loading.stop()

        state["report"] = report
        result.set_results(report_to_results(report))
        stack.setCurrentWidget(result)
        print("[DEBUG] 분석 완료 → 결과 페이지로 전환")

    def on_analysis_error(message: str):
        _stop_progress_timer()
        _wait_for_thread()
        loading.stop()
        print(f"[ERROR] 분석 실패: {message}")
        stack.setCurrentWidget(home)

    def go_to_loading():
        stack.setCurrentWidget(loading)
        loading.update_progress(0)
        loading.start()
        scan_path = home.get_scan_path()
        print(f"[DEBUG] 스캔 요청됨! 대상: {scan_path}")

        thread, worker = start_analysis(scan_path)
        bridge = _AnalysisBridge(on_analysis_finished, on_analysis_error)
        worker.finished.connect(bridge.handle_finished)
        worker.error.connect(bridge.handle_error)
        state["thread"] = thread
        state["worker"] = worker
        state["bridge"] = bridge
        thread.start()

        state["progress_value"] = 0
        progress_timer = QTimer()
        progress_timer.timeout.connect(_tick_progress)
        progress_timer.start(PROGRESS_TICK_MS)
        state["progress_timer"] = progress_timer

    def go_to_detail(category: str):
        report = state["report"]
        if report is None:
            return
        if category == CATEGORY_DELETE_TARGET:
            delete_detail.set_files(report_to_delete_files(report))
            delete_detail.update_responsive_size(window.width())
            stack.setCurrentWidget(delete_detail)
        elif category == CATEGORY_DUPLICATE:
            duplicate_detail.set_groups(report_to_duplicate_groups(report))
            duplicate_detail.update_responsive_size(window.width())
            stack.setCurrentWidget(duplicate_detail)

    home.scan_requested.connect(go_to_loading)
    result.card_clicked.connect(go_to_detail)

    is_dark = load_dark_mode()

    def toggle_theme():
        nonlocal is_dark
        is_dark = not is_dark
        apply_theme(window, dark=is_dark)
        titlebar.apply_icon_colors(dark=is_dark)
        loading.apply_theme(dark=is_dark)
        home.apply_theme(dark=is_dark)
        result.apply_theme(dark=is_dark)
        delete_detail.apply_theme(dark=is_dark)
        duplicate_detail.apply_theme(dark=is_dark)
        save_dark_mode(is_dark)

    titlebar.menu_requested.connect(toggle_theme)

    apply_theme(window, dark=is_dark)
    titlebar.apply_icon_colors(dark=is_dark)
    loading.apply_theme(dark=is_dark)
    home.apply_theme(dark=is_dark)
    result.apply_theme(dark=is_dark)
    delete_detail.apply_theme(dark=is_dark)
    duplicate_detail.apply_theme(dark=is_dark)

    # 폰트 연결
    set_global_scale(window.width())
    window.font_scale_changed.connect(home.refresh_fonts)
    window.font_scale_changed.connect(loading.refresh_fonts)
    window.font_scale_changed.connect(titlebar.refresh_fonts)
    window.font_scale_changed.connect(result.refresh_fonts)
    window.font_scale_changed.connect(delete_detail.refresh_fonts)
    window.font_scale_changed.connect(duplicate_detail.refresh_fonts)
    home.refresh_fonts()
    loading.refresh_fonts()
    titlebar.refresh_fonts()
    result.refresh_fonts()
    delete_detail.refresh_fonts()
    duplicate_detail.refresh_fonts()
    result.update_responsive_size(window.width())

    window.show()

    app.aboutToQuit.connect(lambda: save_dark_mode(is_dark))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
