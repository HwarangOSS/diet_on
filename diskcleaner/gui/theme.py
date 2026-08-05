# 기본 디자인 시스템 & 컬러 팔레트
# 화이트 모드
LIGHT_BG = "#FFFFFF"
LIGHT_TITLE = "#3A4A63"
LIGHT_TEXT = "#101820"
LIGHT_TEXT_GRAY = "#555555"
LIGHT_TEXT_GRAY_LIGHT = "#B9B9B9"

# 다크 모드
DARK_BG = "#101820"
DARK_TITLE = "#FFFFFF"
DARK_TEXT = "#FFFFFF"
DARK_TEXT_GRAY_LIGHT = "#B9B9B9"
DARK_TEXT_GRAY = "#555555"

# 상태 색상 (라이트/다크 공통)
ACCENT_DANGER = "#971B2F"
ACCENT_SUCCESS = "#5A995E"

LIGHT_QSS = f"""
QWidget {{
    background-color: {LIGHT_BG};
    color: {LIGHT_TEXT};
    font-family: "Segoe UI", "Malgun Gothic", sans-serif;
}}

QLabel#titleLabel {{
    color: {LIGHT_TITLE};
    font-weight: 600;
}}

QLabel#clickLabel {{
    color: {LIGHT_TEXT};
    font-size: 16px;
    font-weight: 600;
}}

QLabel#subLabel {{
    color: {LIGHT_TEXT_GRAY};
    font-size: 11px;
}}

QLabel#hintLabel {{
    color: {LIGHT_TEXT_GRAY_LIGHT};
    font-size: 10px;
}}

QFrame#dangerCard {{
    border: 1px solid {ACCENT_DANGER};
    border-radius: 8px;
}}
QLabel#dangerIcon, QLabel#dangerText {{
    color: {ACCENT_DANGER};
}}

QFrame#successCard {{
    border: 1px solid {ACCENT_SUCCESS};
    border-radius: 8px;
}}
QLabel#successIcon, QLabel#successText {{
    color: {ACCENT_SUCCESS};
}}

QFrame#titleSeparator {{
    background: #B9B9B9;
}}

QPushButton#titleIconButton {{
    background: transparent;
    border: none;
    padding: 0;
}}
QPushButton#titleIconButton:hover {{
    background-color: rgba(0, 0, 0, 0.06);
    border-radius: 4px;
}}
"""

DARK_QSS = f"""
QWidget {{
    background-color: {DARK_BG};
    color: {DARK_TEXT};
    font-family: "Segoe UI", "Malgun Gothic", sans-serif;
}}

QLabel#titleLabel {{
    color: {DARK_TITLE};
    font-weight: 600;
}}

QLabel#clickLabel {{
    color: {DARK_TEXT};
    font-size: 16px;
    font-weight: 600;
}}

QLabel#subLabel {{
    color: {DARK_TEXT};
    font-size: 11px;
}}

QLabel#hintLabel {{
    color: {DARK_TEXT_GRAY_LIGHT};
    font-size: 10px;
}}

QFrame#dangerCard {{
    border: 1px solid {ACCENT_DANGER};
    border-radius: 8px;
}}
QLabel#dangerIcon, QLabel#dangerText {{
    color: {ACCENT_DANGER};
}}

QFrame#successCard {{
    border: 1px solid {ACCENT_SUCCESS};
    border-radius: 8px;
}}
QLabel#successIcon, QLabel#successText {{
    color: {ACCENT_SUCCESS};
}}

QFrame#titleSeparator {{
    background: #4A5568;
}}

QPushButton#titleIconButton {{
    background: transparent;
    border: none;
    padding: 0;
}}
QPushButton#titleIconButton:hover {{
    background-color: rgba(255, 255, 255, 0.08);
    border-radius: 4px;
}}
"""


def apply_theme(widget, dark: bool):
    widget.setStyleSheet(DARK_QSS if dark else LIGHT_QSS)
