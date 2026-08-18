REFERENCE_WIDTH = 880

REF_HEIGHT = 100
REF_CORNER_RADIUS = 12

REF_PADDING_H = 16
REF_PADDING_V = 12
REF_ROW_GAP = 6
REF_TOP_ROW_GAP = 8

SELECT_SHADOW_COLOR = "#101820"
REF_GLOW_SPREAD = 4


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
