import os
from PySide6.QtGui import QFontDatabase

FONT_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")

# 폰트 매핑
_FONT_FILES = {
    "Play-Regular": "Play-Regular.ttf",
    "Play-Bold": "Play-Bold.ttf",
    "Pretendard-Thin": "Pretendard-Thin.ttf",
    "Pretendard-ExtraLight": "Pretendard-ExtraLight.ttf",
    "Pretendard-Light": "Pretendard-Light.ttf",
    "Pretendard-Regular": "Pretendard-Regular.ttf",
    "Pretendard-Medium": "Pretendard-Medium.ttf",
    "Pretendard-SemiBold": "Pretendard-SemiBold.ttf",
    "Pretendard-Bold": "Pretendard-Bold.ttf",
    "Pretendard-ExtraBold": "Pretendard-ExtraBold.ttf",
    "Pretendard-Black": "Pretendard-Black.ttf",
}


_loaded_families: dict[str, str] = {}

def load_app_fonts() -> dict[str, str]:
    if _loaded_families:
        return _loaded_families

    for key, filename in _FONT_FILES.items():
        path = os.path.join(FONT_DIR, filename)
        if not os.path.exists(path):
            print(f"폰트 파일 없음: {path}")
            continue

        font_id = QFontDatabase.addApplicationFont(path)
        if font_id == -1:
            print(f" 폰트 로드 실패: {filename}")
            continue

        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            _loaded_families[key] = families[0]

    return _loaded_families
