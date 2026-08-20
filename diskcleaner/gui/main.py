import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStackedWidget, QVBoxLayout

from diskcleaner.core.deletion_pipeline import delete_plan
from diskcleaner.gui.analysis_worker import start_analysis
from diskcleaner.gui.components.titlebar import TitleBar
from diskcleaner.gui.main_window import MainWindow
from diskcleaner.gui.pages.complete import CompletePage
from diskcleaner.gui.pages.delete_detail import DeletePage
from diskcleaner.gui.pages.duplicate_detail import DuplicatePage
from diskcleaner.gui.pages.home import HomePage
from diskcleaner.gui.pages.info import InfoPage
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

HELP_TITLE = "도움말"
HELP_TEXT = """실행 방법

1. 스캔할 경로 선택 (기본값: 시스템 드라이브 루트)
2. 스캔 시작 → 파일 분석 완료까지 대기
3. 결과 화면에서 안전 삭제 대상 / 중복 파일 / AI 분석 대상 확인
4. 원클릭 일괄 삭제 또는 상세 화면에서 개별 선택 후 삭제

AI 삭제 권장 기능을 쓰려면 ANTHROPIC_API_KEY 환경변수가 설정되어 있어야 합니다.
설정하지 않아도 실행은 되며, 이 경우 기본 규칙 기반 권장만 제공됩니다."""

LICENSE_TITLE = "라이센스"
LICENSE_TEXT = """이 프로그램(DietOn)은 gccszs/disk-cleaner 프로젝트를 포크하여 제작되었습니다.
원본 프로젝트 및 본 프로그램 모두 MIT License를 따릅니다.

MIT License

Copyright (c) 2025 Disk Cleaner Contributors
Copyright (c) 2026 HwarangOSS (DietOn)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""


def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


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

    if sys.platform == "win32":
        import ctypes

        myappid = "hwarangoss.dieton.app.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("assets/icon/icon.ico")))

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
    info_page = InfoPage()

    stack.addWidget(home)
    stack.addWidget(loading)
    stack.addWidget(result)
    stack.addWidget(delete_detail)
    stack.addWidget(duplicate_detail)
    stack.addWidget(complete)
    stack.addWidget(info_page)

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
        "pre_info_widget": None,
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

    def go_to_complete():
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
        stack.setCurrentWidget(complete)
        result_ = delete_plan(plan, deletion_manager, set(selected_paths))
        print(
            f"[삭제] {result_.total_deleted}개 삭제, {result_.total_failed}개 실패, "
            f"{result_.total_size_freed / (1024**2):.1f}MB 확보"
        )
        _refresh_after_deletion(result_)
        go_to_complete()

    def on_duplicate_delete_requested(selected_paths):
        if not selected_paths:
            return
        stack.setCurrentWidget(complete)
        result_ = deletion_manager.delete([Path(p) for p in selected_paths])
        print(
            f"[삭제] {result_.total_deleted}개 삭제, {result_.total_failed}개 실패, "
            f"{result_.total_size_freed / (1024**2):.1f}MB 확보"
        )
        _refresh_after_deletion(result_)
        go_to_complete()

    def on_complete_result_requested():
        stack.setCurrentWidget(result)

    def go_to_info(title: str, body: str):
        current = stack.currentWidget()
        if current is not info_page:
            state["pre_info_widget"] = current
        info_page.set_content(title, body)
        info_page.update_responsive_size(window.width())
        stack.setCurrentWidget(info_page)

    def on_info_back_requested():
        stack.setCurrentWidget(state["pre_info_widget"] or home)

    home.scan_requested.connect(go_to_loading)
    result.card_clicked.connect(go_to_detail)
    delete_detail.delete_requested.connect(on_delete_target_delete_requested)
    duplicate_detail.delete_requested.connect(on_duplicate_delete_requested)
    delete_detail.back_requested.connect(lambda: stack.setCurrentWidget(result))
    duplicate_detail.back_requested.connect(lambda: stack.setCurrentWidget(result))
    complete.result_requested.connect(on_complete_result_requested)
    info_page.back_requested.connect(on_info_back_requested)
    titlebar.help_requested.connect(lambda: go_to_info(HELP_TITLE, HELP_TEXT))
    titlebar.license_requested.connect(lambda: go_to_info(LICENSE_TITLE, LICENSE_TEXT))

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
        info_page.apply_theme(dark=is_dark)
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
    info_page.apply_theme(dark=is_dark)

    # 폰트 연결
    set_global_scale(window.width())
    window.font_scale_changed.connect(home.refresh_fonts)
    window.font_scale_changed.connect(loading.refresh_fonts)
    window.font_scale_changed.connect(titlebar.refresh_fonts)
    window.font_scale_changed.connect(result.refresh_fonts)
    window.font_scale_changed.connect(delete_detail.refresh_fonts)
    window.font_scale_changed.connect(duplicate_detail.refresh_fonts)
    window.font_scale_changed.connect(complete.refresh_fonts)
    window.font_scale_changed.connect(info_page.refresh_fonts)
    home.refresh_fonts()
    loading.refresh_fonts()
    titlebar.refresh_fonts()
    result.refresh_fonts()
    delete_detail.refresh_fonts()
    duplicate_detail.refresh_fonts()
    complete.refresh_fonts()
    info_page.refresh_fonts()
    result.update_responsive_size(window.width())

    window.show()

    app.aboutToQuit.connect(lambda: save_dark_mode(is_dark))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
