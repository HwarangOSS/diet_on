# 디자인 토큰
from PySide6.QtGui import QFont

from .fonts import load_app_fonts

_current_scale = 1.0
BASE_WINDOW_WIDTH = 500

MIN_FONT_PT = 6

_LETTER_SPACING = {
    "headline": 0.2,
    "headline_small": 0.2,
    "path_quote": 0.1,
    "naming": 0.1,
    "group": 0.1,
    "body_md": 0.1,
    "body_mini": 0.2,
    "hashtag": 0.4,
    "trust": 0.4,
    "ver": 0.3,
}


# 폰트 비율
def set_global_scale(window_width: int):
    global _current_scale
    scale = window_width / BASE_WINDOW_WIDTH
    _current_scale = max(0.6, min(scale, 1.5))


def get_global_scale() -> float:
    return _current_scale


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


def get_font(family_key: str, size: int, bold: bool = False, role: str | None = None) -> QFont:
    families = load_app_fonts()
    family_name = families.get(family_key, "Arial")
    scaled_size = max(MIN_FONT_PT, int(size * _current_scale))
    font = QFont(family_name, scaled_size)
    font.setBold(bold)

    spacing = _LETTER_SPACING.get(role, 0.0)
    if spacing:
        font.setLetterSpacing(QFont.AbsoluteSpacing, spacing * _current_scale)
    return font


# Play ----------------------------------
# 메인 타이틀 / 로딩 / 클릭
def headline() -> QFont:
    return get_font(FontFamily.PLAY_REGULAR, 20, role="headline")


# 홈 화면 - 검사 대상 경로를 굵게 인용부호로 보여줄 때 (목업 "C://user/mings")
def path_quote() -> QFont:
    return get_font(FontFamily.PLAY_BOLD, 13, role="path_quote")


# 삭제 & 중복 소제목
def headline_small() -> QFont:
    return get_font(FontFamily.PLAY_REGULAR, 16, role="headline_small")


# 해시태그
def hashtag() -> QFont:
    return get_font(FontFamily.PLAY_REGULAR, 7, role="hashtag")


# 신뢰도
def trust() -> QFont:
    return get_font(FontFamily.PLAY_REGULAR, 6, role="trust")


# Pretendard ----------------------------------

def naming() -> QFont:
    return get_font(FontFamily.PRETENDARD_MEDIUM, 11, role="naming")


# 그룹화
def group() -> QFont:
    return get_font(FontFamily.PRETENDARD_BOLD, 8, role="group")


# 기본 텍스트 & 파일 경로
def body_md() -> QFont:
    return get_font(FontFamily.PRETENDARD_REGULAR, 8, role="body_md")


# 용량 표시 & 더보기
def body_mini() -> QFont:
    return get_font(FontFamily.PRETENDARD_REGULAR, 7, role="body_mini")


# 버전
def ver() -> QFont:
    return get_font(FontFamily.PRETENDARD_REGULAR, 6, role="ver")
