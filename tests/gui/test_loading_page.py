# 테스트코드
from diskcleaner.gui.pages.loading import LoadingPage


def test_update_progress_emits_analyze_finished_at_100(qtbot):
    page = LoadingPage()
    qtbot.addWidget(page)

    received = []
    page.analyze_finished.connect(lambda: received.append(True))

    page.update_progress(50)
    assert received == []

    page.update_progress(100)
    assert received == [True]


def test_update_progress_moves_progress_bar_to_target_value(qtbot):
    page = LoadingPage()
    qtbot.addWidget(page)

    page.update_progress(42)

    qtbot.waitUntil(lambda: page.progress_bar.progress == 42, timeout=1000)
