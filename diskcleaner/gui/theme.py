# 디자인 시스템 & 컬러 팔레트
from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    """라이트/다크 테마 하나의 색상 세트."""

    bg: str  # 배경
    surface: str  # 모달
    border: str  # 기본 구분선
    border_strong: str  # 강조 구분선

    # 텍스트
    text_primary: str  # 본문
    text_secondary: str  # 설명
    text_tertiary: str  # 힌트, 캡션, 버전 표기 등
    title: str

    # 인터랙티브
    primary: str
    primary_hover: str

    # 상태
    danger: str
    danger_surface: str  # danger 카드 배경
    success: str
    success_surface: str  # success 카드 배경

    # hover
    hover_overlay: str
    pressed_overlay: str


LIGHT = Palette(
    bg="#FFFFFF",
    surface="#F5F6F8",
    border="#E2E4E9",
    border_strong="#C7CBD4",
    text_primary="#101820",
    text_secondary="#555555",
    text_tertiary="#767676",
    title="#3A4A63",
    primary="#3A4A63",
    primary_hover="#2C3A4F",
    danger="#971B2F",
    danger_surface="rgba(151, 27, 47, 0.06)",
    success="#5A995E",
    success_surface="rgba(90, 153, 94, 0.08)",
    hover_overlay="rgba(0, 0, 0, 0.06)",
    pressed_overlay="rgba(0, 0, 0, 0.10)",
)

DARK = Palette(
    bg="#101820",
    surface="#1A2430",
    border="#2B3A4A",
    border_strong="#4A5568",
    text_primary="#F2F4F7",
    text_secondary="#B9B9B9",
    text_tertiary="#8A93A3",
    title="#FFFFFF",
    primary="#7C9CBF",
    primary_hover="#9AB4D1",
    danger="#E5566E",
    danger_surface="rgba(229, 86, 110, 0.10)",
    success="#7CC183",
    success_surface="rgba(124, 193, 131, 0.10)",
    hover_overlay="rgba(255, 255, 255, 0.08)",
    pressed_overlay="rgba(255, 255, 255, 0.14)",
)


def _build_qss(p: Palette, dark: bool) -> str:
    return f"""
QWidget {{
    background-color: {p.bg};
    color: {p.text_primary};
    font-family: "Segoe UI", "Malgun Gothic", sans-serif;
}}

QLabel#titleLabel {{
    color: {p.title};
}}

QLabel#clickLabel {{
    color: {p.text_primary};
}}

QLabel#pathQuoteLabel {{
    color: {p.title};
}}

QLabel#subLabel {{
    color: {p.text_secondary};
}}

QLabel#hintLabel, QLabel#scanPathLabel {{
    color: {p.text_tertiary};
}}

QFrame#dangerCard {{
    background-color: {p.danger_surface};
    border: 1px solid {p.danger};
    border-radius: 8px;
}}
QLabel#dangerIcon, QLabel#dangerText {{
    color: {p.danger};
}}

QFrame#successCard {{
    background-color: {p.success_surface};
    border: 1px solid {p.success};
    border-radius: 8px;
}}
QLabel#successIcon, QLabel#successText {{
    color: {p.success};
}}

QFrame#titleSeparator {{
    background: {p.border_strong};
}}

QPushButton#titleIconButton {{
    background: transparent;
    border: none;
    padding: 0;
}}
QPushButton#titleIconButton:hover {{
    background-color: {p.hover_overlay};
    border-radius: 4px;
}}
QPushButton#titleIconButton:pressed {{
    background-color: {p.pressed_overlay};
    border-radius: 4px;
}}

QLabel#loadingTitle {{
    color: {p.text_primary};
}}
QLabel#loadingMessage {{
    color: {p.text_secondary};
}}
QLabel#loadingPathLabel {{
    color: {p.text_tertiary};
}}

QFrame#card {{
    background-color: {p.surface};
    border: 1px solid {p.border};
    border-radius: 8px;
}}

QLabel#statusMessage {{
    color: {p.text_primary};
}}
QLabel#statusMeta {{
    color: {p.text_secondary};
}}

QLabel#resultCapacityLabel {{
    color: {"#FFFFFF" if dark else p.text_secondary};
}}
QLabel#resultGbLabel {{
    color: {"#FFFFFF" if dark else p.text_primary};
}}
QLabel#resultHeading {{
    color: {"#FFFFFF" if dark else p.text_primary};
}}
QLabel#resultPathLabel {{
    color: {p.text_tertiary};
}}

QLabel#detailTitle {{
    color: {"#FFFFFF" if dark else p.text_primary};
}}
QLabel#detailBackLabel {{
    color: {p.primary};
}}
QLabel#deleteGroupTitle {{
    color: {p.text_secondary};
}}
QCheckBox#deleteGroupCheckbox {{
    color: {p.primary};
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {p.border_strong};
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {p.text_tertiary};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""


LIGHT_QSS = _build_qss(LIGHT, dark=False)
DARK_QSS = _build_qss(DARK, dark=True)


def apply_theme(widget, dark: bool):
    widget.setStyleSheet(DARK_QSS if dark else LIGHT_QSS)


def palette_for(dark: bool) -> Palette:
    return DARK if dark else LIGHT
