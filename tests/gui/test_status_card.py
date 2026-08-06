# 테스트 코드
from PySide6.QtCore import Qt

from diskcleaner.gui.components.status_card import STATUS_DANGER, StatusCard


def test_set_result_updates_labels(qtbot):
    card = StatusCard()
    qtbot.addWidget(card)

    card.set_result(STATUS_DANGER, "테스트 메시지", 3, 512 * 1024 * 1024)

    assert card.message_label.text() == "테스트 메시지"
    assert card.meta_label.text() == "3개 (0.5GB)"


def test_clicked_signal_emitted_on_press_release_inside(qtbot):
    card = StatusCard()
    qtbot.addWidget(card)

    with qtbot.waitSignal(card.clicked, timeout=1000):
        qtbot.mousePress(card, Qt.LeftButton, pos=card.rect().center())
        qtbot.mouseRelease(card, Qt.LeftButton, pos=card.rect().center())
