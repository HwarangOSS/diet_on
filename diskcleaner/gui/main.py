import sys
from pathlib import Path

from dotenv import load_dotenv
from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication, QStackedWidget, QVBoxLayout

from diskcleaner.core.deletion_pipeline import delete_plan
from diskcleaner.gui.analysis_worker import start_analysis
from diskcleaner.gui.components.titlebar import TitleBar
from diskcleaner.gui.main_window import MainWindow
from diskcleaner.gui.pages.complete import CompletePage
from diskcleaner.gui.pages.delete_detail import DeletePage
from diskcleaner.gui.pages.duplicate_detail import DuplicatePage
from diskcleaner.gui.pages.home import HomePage
from diskcleaner.gui.pages.loading import LoadingPage
from diskcleaner.gui.pages.result import CATEGORY_DELETE_TARGET, CATEGORY_DUPLICATE, ResultPage
from diskcleaner.gui.result_mapping import (
    remove_deleted_paths,
    report_to_delete_files,
    report_to_duplicate_groups,
    report_to_results,
)
from diskcleaner.gui.settings import load_dark_mode, save_dark_mode
from diskcleaner.gui.theme import apply_theme
from diskcleaner.gui.typo import set_global_scale
from diskcleaner.optimization.delete import DeletionManager

PROGRESS_TICK_MS = 200
PROGRESS_TICK_STEP = 3
PROGRESS_TICK_CAP = 90


class _AnalysisBridge(QObject):
    def __init__(self, on_finished, on_error):
        super().__init__()
        self._on_finished = on_finished
        self._on_error = on_error

    def handle_finished(self, report, plan):
        self._on_finished(report, plan)

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
    complete = CompletePage()

    stack.addWidget(home)
    stack.addWidget(loading)
    stack.addWidget(result)
    stack.addWidget(delete_detail)
    stack.addWidget(duplicate_detail)
    stack.addWidget(complete)

    root_layout.addWidget(stack)

    state = {
        "thread": None,
        "worker": None,
        "bridge": None,
        "progress_timer": None,
        "progress_value": 0,
        "report": None,
        "plan": None,
        "scan_path": None,
    }
    deletion_manager = DeletionManager()

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
            print(f"{state['progress_value']}%")

    def on_analysis_finished(report, plan):
        _stop_progress_timer()
        _wait_for_thread()
        loading.update_progress(100)
        loading.stop()

        state["report"] = report
        state["plan"] = plan
        result.set_path(state["scan_path"])
        result.set_results(report_to_results(report, plan))
        stack.setCurrentWidget(result)
        print("분석 완료 → 결과 페이지로 전환")

    def on_analysis_error(message: str):
        _stop_progress_timer()
        _wait_for_thread()
        loading.stop()
        print(f"[ERROR]: {message}")
        stack.setCurrentWidget(home)

    def go_to_loading():
        stack.setCurrentWidget(loading)
        loading.update_progress(0)
        scan_path = home.get_scan_path()
        state["scan_path"] = scan_path
        loading.set_path(scan_path)
        loading.start()
        print(f"스캔 요청됨! 대상: {scan_path}")

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
            delete_detail.set_files(report_to_delete_files(report, state["plan"]))
            delete_detail.update_responsive_size(window.width())
            stack.setCurrentWidget(delete_detail)
        elif category == CATEGORY_DUPLICATE:
            duplicate_detail.set_groups(report_to_duplicate_groups(report))
            duplicate_detail.update_responsive_size(window.width())
            stack.setCurrentWidget(duplicate_detail)

    def go_to_complete(result_):
        complete.set_result(result_.total_deleted, result_.total_size_freed)
        complete.update_responsive_size(window.width())
        stack.setCurrentWidget(complete)

    def _refresh_after_deletion(result_):
        deleted_paths = {str(p) for p in result_.success}
        remove_deleted_paths(state["report"], state["plan"], deleted_paths)
        result.set_results(report_to_results(state["report"], state["plan"]))

    def on_delete_target_delete_requested(selected_paths):
        plan = state["plan"]
        if plan is None or not selected_paths:
            return
        result_ = delete_plan(plan, deletion_manager, set(selected_paths))
        print(
            f"[삭제] {result_.total_deleted}개 삭제, {result_.total_failed}개 실패, "
            f"{result_.total_size_freed / (1024**2):.1f}MB 확보"
        )
        _refresh_after_deletion(result_)
        go_to_complete(result_)

    def on_duplicate_delete_requested(selected_paths):
        if not selected_paths:
            return
        result_ = deletion_manager.delete([Path(p) for p in selected_paths])
        print(
            f"[삭제] {result_.total_deleted}개 삭제, {result_.total_failed}개 실패, "
            f"{result_.total_size_freed / (1024**2):.1f}MB 확보"
        )
        _refresh_after_deletion(result_)
        go_to_complete(result_)

    def on_complete_result_requested():
        stack.setCurrentWidget(result)

    home.scan_requested.connect(go_to_loading)
    result.card_clicked.connect(go_to_detail)
    delete_detail.delete_requested.connect(on_delete_target_delete_requested)
    duplicate_detail.delete_requested.connect(on_duplicate_delete_requested)
    delete_detail.back_requested.connect(lambda: stack.setCurrentWidget(result))
    duplicate_detail.back_requested.connect(lambda: stack.setCurrentWidget(result))
    complete.result_requested.connect(on_complete_result_requested)

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
        complete.apply_theme(dark=is_dark)
        save_dark_mode(is_dark)

    titlebar.menu_requested.connect(toggle_theme)

    apply_theme(window, dark=is_dark)
    titlebar.apply_icon_colors(dark=is_dark)
    loading.apply_theme(dark=is_dark)
    home.apply_theme(dark=is_dark)
    result.apply_theme(dark=is_dark)
    delete_detail.apply_theme(dark=is_dark)
    duplicate_detail.apply_theme(dark=is_dark)
    complete.apply_theme(dark=is_dark)

    # 폰트 연결
    set_global_scale(window.width())
    window.font_scale_changed.connect(home.refresh_fonts)
    window.font_scale_changed.connect(loading.refresh_fonts)
    window.font_scale_changed.connect(titlebar.refresh_fonts)
    window.font_scale_changed.connect(result.refresh_fonts)
    window.font_scale_changed.connect(delete_detail.refresh_fonts)
    window.font_scale_changed.connect(duplicate_detail.refresh_fonts)
    window.font_scale_changed.connect(complete.refresh_fonts)
    home.refresh_fonts()
    loading.refresh_fonts()
    titlebar.refresh_fonts()
    result.refresh_fonts()
    delete_detail.refresh_fonts()
    duplicate_detail.refresh_fonts()
    complete.refresh_fonts()
    result.update_responsive_size(window.width())

    window.show()

    app.aboutToQuit.connect(lambda: save_dark_mode(is_dark))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
