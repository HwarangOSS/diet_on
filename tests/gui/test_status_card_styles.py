# 테스트 코드
from diskcleaner.gui.components.status_card.styles import format_gb


def test_format_gb_zero():
    assert format_gb(0) == "0GB"


def test_format_gb_whole_number():
    assert format_gb(1024**3) == "1GB"


def test_format_gb_rounds_to_one_decimal():
    assert format_gb(int(2.5 * 1024**3)) == "2.5GB"
