# 백그라운드 QThread에서 돌리기 위한 워커

import time

from PySide6.QtCore import QObject, QThread, Signal

from diskcleaner.core.deletion_pipeline import DeletionPlan, build_deletion_plan
from diskcleaner.core.smart_cleanup import CleanupReport, SmartCleanupEngine


class AnalysisWorker(QObject):

    finished = Signal(CleanupReport, DeletionPlan)
    error = Signal(str)

    def __init__(self, target_path: str):
        super().__init__()
        self.target_path = target_path

    def run(self):
        print(f"분석 시작: {self.target_path}")
        start = time.monotonic()
        try:
            engine = SmartCleanupEngine(self.target_path)
            report = engine.analyze()
            duplicate_paths = {
                f.path for group in report.duplicates for f in group.files
            }
            candidates = [
                f
                for f in report.by_risk.get("safe", []) + report.by_risk.get("confirm_needed", [])
                if f.path not in duplicate_paths
            ]
            plan = build_deletion_plan(candidates)
        except Exception as exc:
            print(f"[SCAN] 실패 ({time.monotonic() - start:.1f}s): {exc}")
            self.error.emit(str(exc))
            return
        print(
            f"완료 ({time.monotonic() - start:.1f}s) - "
            f"파일 {report.total_files}개, 중복 {len(report.duplicates)}그룹, "
            f"확보 가능한 용량 {report.total_reclaimable / (1024**3):.2f}GB, "
            f"AI 자동삭제 {len(plan.auto_delete)}개, 검토대기 {len(plan.review_queue)}개"
        )
        self.finished.emit(report, plan)


def start_analysis(target_path: str) -> tuple[QThread, AnalysisWorker]:
    thread = QThread()
    worker = AnalysisWorker(target_path)
    worker.moveToThread(thread)

    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    worker.error.connect(thread.quit)

    return thread, worker
