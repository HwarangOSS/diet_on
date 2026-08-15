# 테스트코드
from diskcleaner.core.deletion_pipeline import delete_plan
from diskcleaner.core.smart_cleanup import SmartCleanupEngine
from diskcleaner.gui.analysis_worker import AnalysisWorker
from diskcleaner.optimization.delete import DeletionManager
from tests.gui.factories import make_report


def test_worker_emits_finished_with_report_and_plan(qtbot, monkeypatch, tmp_path):
    fake_report = make_report()
    monkeypatch.setattr(SmartCleanupEngine, "analyze", lambda self, **kwargs: fake_report)

    worker = AnalysisWorker(str(tmp_path))

    with qtbot.waitSignal(worker.finished, timeout=1000) as blocker:
        worker.run()

    report, plan = blocker.args
    assert report is fake_report
    assert plan.auto_delete == []
    assert plan.review_queue == []
    assert plan.excluded == []


def test_worker_dummy_file_end_to_end_scan_and_delete(qtbot, tmp_path):
    """이슈 #17 TODO: 더미 파일로 스캔->AI 삭제 계획->실제 삭제까지 전체 연동 확인.

    LLM 호출을 피하려고 classifier가 confirm_needed로 분류하지 않는 확장자(.cache)만 씀.
    """
    dummy = tmp_path / "leftover.cache"
    dummy.write_text("x" * 10)

    worker = AnalysisWorker(str(tmp_path))
    with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
        worker.run()
    report, plan = blocker.args

    assert report.total_files == 1
    assert [f.name for f in plan.auto_delete] == ["leftover.cache"]

    confirmed_paths = {f.path for f in plan.auto_delete}
    result = delete_plan(plan, DeletionManager(), confirmed_paths)

    assert result.total_deleted == 1
    assert not dummy.exists()


def test_worker_emits_error_on_exception(qtbot, monkeypatch, tmp_path):
    def boom(self, **kwargs):
        raise RuntimeError("스캔 실패")

    monkeypatch.setattr(SmartCleanupEngine, "analyze", boom)

    worker = AnalysisWorker(str(tmp_path))

    with qtbot.waitSignal(worker.error, timeout=1000) as blocker:
        worker.run()

    assert blocker.args == ["스캔 실패"]
