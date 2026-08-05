# 디자인 토큰
from PySide6.QtGui import QFont
from .fonts import load_app_fonts

class FontFamily:
    PLAY_REGULAR = "Play-Regular"
    PLAY_BOLD = "Play-Bold"
    PRETENDARD_THIN = "Pretendard-Thin"
    PRETENDARD_EXTRALIGHT = "Pretendard-ExtraLight"
    PRETENDARD_LIGHT = "Pretendard-Light"
    PRETENDARD_REGULAR = "Pretendard-Regular"
    PRETENDARD_MEDIUM = "Pretendard-Medium"
    PRETENDARD_SEMIBOLD = "Pretendard-SemiBold"
    PRETENDARD_BOLD = "Pretendard-Bold"
    PRETENDARD_EXTRABOLD = "Pretendard-ExtraBold"
    PRETENDARD_BLACK = "Pretendard-Black"


def get_font(family_key: str, size: int, bold: bool = False) -> QFont:
    families = load_app_fonts()
    family_name = families.get(family_key, "Arial")
    font = QFont(family_name, size)
    font.setBold(bold)
    return font


# 메인 타이틀 / 로딩 / 클릭 / 남은 GB
def play_large() -> QFont:
    return get_font(FontFamily.PLAY_REGULAR, 40)

def titlebar_title() -> QFont:
    return get_font(FontFamily.PLAY_BOLD, 18) 

# Delete & Duplicate 소제목
def play_medium() -> QFont:
    return get_font(FontFamily.PLAY_REGULAR, 32)

# 각 리스트 파일명
def body_mini_title() -> QFont:
    return get_font(FontFamily.PRETENDARD_REGULAR, 22)

# 기본 폰트(미분류 된거)
def body() -> QFont:
    return get_font(FontFamily.PRETENDARD_REGULAR, 18)

# 항목별 용량
def body_medium() -> QFont:
    return get_font(FontFamily.PRETENDARD_REGULAR, 14)

# 해시태그
def hashtag() -> QFont:
    return get_font(FontFamily.PRETENDARD_REGULAR, 12)

# 중복항목 묶기 타이틀
def duplicate() -> QFont:
    return get_font(FontFamily.PRETENDARD_BOLD, 14)
