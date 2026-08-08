BASE_WIDTH = 463
BASE_HEIGHT = 108
CORNER_RADIUS = 12

BASE_PADDING_H = 16
BASE_PADDING_V = 14
BASE_ROW_GAP = 6

SELECT_SHADOW_COLOR = "#101820"
GLOW_SPREAD = 4

SCALE_MIN = 0.6
SCALE_MAX = 1.5


def format_file_size(size_bytes: int) -> str:
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024.0 or unit == "TB":
            if unit == "B":
                return f"{int(size)}{unit}"
            rounded = round(size, 1)
            if rounded == int(rounded):
                return f"{int(rounded)}{unit}"
            return f"{rounded}{unit}"
        size /= 1024.0
    return f"{size:.1f}TB"
