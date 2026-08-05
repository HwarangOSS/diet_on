from PySide6.QtCore import QSettings

_ORG = "HwarangOSS"
_APP = "DietOn"

# 마지막 사용 테마
def load_dark_mode() -> bool:
    settings = QSettings(_ORG, _APP)
    return settings.value("dark_mode", False, type=bool)

def save_dark_mode(dark: bool) -> None:
    settings = QSettings(_ORG, _APP)
    settings.setValue("dark_mode", dark)
