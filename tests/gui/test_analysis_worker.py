# 테스트코드
from diskcleaner.core.smart_cleanup import SmartCleanupEngine
from diskcleaner.gui.analysis_worker import AnalysisWorker
from tests.gui.factories import make_report


def test_worker_emits_finished_with_report(qtbot, monkeypatch, tmp_path):
    fake_report = make_report()
    monkeypatch.setattr(SmartCleanupEngine, "analyze", lambda self, **kwargs: fake_report)

    worker = AnalysisWorker(str(tmp_path))

    with qtbot.waitSignal(worker.finished, timeout=1000) as blocker:
        worker.run()

    assert blocker.args == [fake_report]


def test_worker_emits_error_on_exception(qtbot, monkeypatch, tmp_path):
    def boom(self, **kwargs):
        raise RuntimeError("스캔 실패")

    monkeypatch.setattr(SmartCleanupEngine, "analyze", boom)

    worker = AnalysisWorker(str(tmp_path))

    with qtbot.waitSignal(worker.error, timeout=1000) as blocker:
        worker.run()

    assert blocker.args == ["스캔 실패"]
