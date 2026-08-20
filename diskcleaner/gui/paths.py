import os
import sys

_GUI_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR = getattr(sys, "_MEIPASS", _GUI_DIR)


def asset_path(*parts: str) -> str:
    """gui/assets/ 아래 리소스 경로. PyInstaller 빌드(_MEIPASS)와 소스 실행 둘 다 지원."""
    return os.path.join(_BASE_DIR, "assets", *parts)
