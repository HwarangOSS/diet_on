import os

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

ICON_SIZE = 140

SVG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "svgs")

# file1.svg와 file2.svg는 원본 비율이 서로 달라(277:230 vs 304:234), 각자 비율대로
# 맞추면 로딩 중 아이콘이 번갈아 바뀔 때마다 크기가 미묘하게 커졌다 작아졌다 함.
# 두 아이콘 모두 이 기준 비율 하나로 맞춰서 항상 같은 크기로 보이게 함.
_REFERENCE_ASPECT_FILE = "file2.svg"
_reference_aspect: float | None = None


def _load_svg_bytes(filename: str) -> QByteArray:
    path = os.path.join(SVG_DIR, filename)
    if not os.path.exists(path):
        print(f"[WARN] SVG 파일 없음: {path}")
        return QByteArray()

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return QByteArray(content.encode("utf-8"))


def _get_reference_aspect() -> float:
    global _reference_aspect
    if _reference_aspect is None:
        size = QSvgRenderer(_load_svg_bytes(_REFERENCE_ASPECT_FILE)).defaultSize()
        _reference_aspect = size.width() / size.height() if not size.isEmpty() else 1.0
    return _reference_aspect


def _render_pixmap_from_file(filename: str, max_size: int = ICON_SIZE, scale: int = 3) -> QPixmap:
    svg_bytes = _load_svg_bytes(filename)
    renderer = QSvgRenderer(svg_bytes)

    ratio = _get_reference_aspect()
    if ratio >= 1:
        w = max_size
        h = int(max_size / ratio)
    else:
        h = max_size
        w = int(max_size * ratio)

    render_w, render_h = w * scale, h * scale

    pixmap = QPixmap(render_w, render_h)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter, QRectF(0, 0, render_w, render_h))
    painter.end()

    pixmap.setDevicePixelRatio(scale)
    return pixmap


def make_file1_icon(size: int = ICON_SIZE) -> QPixmap:
    return _render_pixmap_from_file("file1.svg", max_size=size)


def make_file2_icon(size: int = ICON_SIZE) -> QPixmap:
    return _render_pixmap_from_file("file2.svg", max_size=size)
