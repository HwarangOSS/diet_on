# 테스트코드
from PySide6.QtCore import Qt

from diskcleaner.gui.pages.result import (
    CARD_TEXTS,
    CATEGORY_DELETE_TARGET,
    CATEGORY_DUPLICATE,
    ResultPage,
)

SAMPLE_RESULTS = {
    "delete_target": {"count": 5, "size_bytes": 1_073_741_824},
    "duplicate": {"count": 0, "size_bytes": 0},
}


def test_set_results_updates_summary_and_cards(qtbot):
    page = ResultPage()
    qtbot.addWidget(page)

    page.set_results(SAMPLE_RESULTS)

    assert page.gb_label.text() == "1GB"

    delete_card = page._cards[CATEGORY_DELETE_TARGET]
    duplicate_card = page._cards[CATEGORY_DUPLICATE]

    assert delete_card.meta_label.text() == "5개 (1GB)"
    assert delete_card.message_label.text() == CARD_TEXTS[CATEGORY_DELETE_TARGET]["found"]

    assert duplicate_card.meta_label.text() == "0개 (0GB)"
    assert duplicate_card.message_label.text() == CARD_TEXTS[CATEGORY_DUPLICATE]["empty"]


def test_card_click_emits_category_key(qtbot):
    page = ResultPage()
    qtbot.addWidget(page)
    page.set_results(SAMPLE_RESULTS)

    card = page._cards[CATEGORY_DELETE_TARGET]

    with qtbot.waitSignal(page.card_clicked, timeout=1000) as blocker:
        qtbot.mousePress(card, Qt.LeftButton, pos=card.rect().center())
        qtbot.mouseRelease(card, Qt.LeftButton, pos=card.rect().center())

    assert blocker.args == [CATEGORY_DELETE_TARGET]
