# 디자인 토큰
from PySide6.QtGui import QFont

from .fonts import load_app_fonts

# 전역 반응형
_current_scale = 1.0
BASE_WINDOW_WIDTH = 500


# 폰트 비율
def set_global_scale(window_width: int):
    global _current_scale
    scale = window_width / BASE_WINDOW_WIDTH
    _current_scale = max(0.6, min(scale, 1.5))


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
    scaled_size = max(1, int(size * _current_scale))
    font = QFont(family_name, scaled_size)
    font.setBold(bold)
    return font


# Play ----------------------------------
# 메인 타이틀 / 로딩 / 클릭
def headline() -> QFont:
    return get_font(FontFamily.PLAY_REGULAR, 20)


# 삭제 & 중복 소제목
def headline_small() -> QFont:
    return get_font(FontFamily.PLAY_REGULAR, 16)


# 해시태그
def hashtag() -> QFont:
    return get_font(FontFamily.PLAY_REGULAR, 6)


# 신뢰도
def trust() -> QFont:
    return get_font(FontFamily.PLAY_REGULAR, 4)


# Pretendard ----------------------------------


# 파일명
def naming() -> QFont:
    return get_font(FontFamily.PRETENDARD_REGULAR, 20)


# 그룹화
def group() -> QFont:
    return get_font(FontFamily.PRETENDARD_BOLD, 8)


# 기본 텍스트 & 파일 경로
def body_md() -> QFont:
    return get_font(FontFamily.PRETENDARD_REGULAR, 8)


# 용량 표시 & 더보기
def body_mini() -> QFont:
    return get_font(FontFamily.PRETENDARD_REGULAR, 6)


# 버전
def ver() -> QFont:
    return get_font(FontFamily.PRETENDARD_REGULAR, 4)
