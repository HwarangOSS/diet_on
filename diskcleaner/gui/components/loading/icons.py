import os

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

ICON_SIZE = 140

SVG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "svgs")


def _load_svg_bytes(filename: str) -> QByteArray:
    path = os.path.join(SVG_DIR, filename)
    if not os.path.exists(path):
        print(f"[WARN] SVG 파일 없음: {path}")
        return QByteArray()

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return QByteArray(content.encode("utf-8"))


def _render_pixmap_from_file(filename: str, max_size: int = ICON_SIZE, scale: int = 3) -> QPixmap:
    svg_bytes = _load_svg_bytes(filename)
    renderer = QSvgRenderer(svg_bytes)

    default_size = renderer.defaultSize()
    if default_size.isEmpty():
        w, h = max_size, max_size
    else:
        ratio = default_size.width() / default_size.height()
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
