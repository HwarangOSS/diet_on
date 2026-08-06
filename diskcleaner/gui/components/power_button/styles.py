from PySide6.QtGui import QColor

from diskcleaner.gui.theme import palette_for


# 배경
# 기존엔 #3A4A63 고정값이라 다크 모드 배경(#101820)과 대비가 거의 없어
# (대비비 ≈ 2:1) 홈 화면의 핵심 CTA 버튼이 사실상 안 보였음.
# palette의 primary를 그대로 써서 모드별로 갈라지게 함 (다크에선 밝은 톤).
def bg_color(dark: bool) -> QColor:
    return QColor(palette_for(dark).primary)


GLOW_COLOR = QColor(255, 255, 255, 128)

# 사이즈 & 비율
BASE_CANVAS_SIZE = 500
DEFAULT_BUTTON_SIZE = 98
BUTTON_RATIO = DEFAULT_BUTTON_SIZE / BASE_CANVAS_SIZE
ICON_RATIO = 0.55

# 반응형
MIN_RESPONSIVE_CANVAS = 250

# 글로우 타입
GLOW_INNER_STOP = 0.55
GLOW_OUTER_STOP = 1.0

# 애니메이션
PRESS_SCALE = 0.92
PRESS_ANIM_DURATION_MS = 180
