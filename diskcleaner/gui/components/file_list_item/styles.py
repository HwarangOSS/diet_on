# rem 단위(1rem=16px)
WIDTH_REM = 463 / 16
HEIGHT_REM = 108 / 16
CORNER_RADIUS_REM = 12 / 16

PADDING_H_REM = 16 / 16
PADDING_V_REM = 14 / 16
ROW_GAP_REM = 6 / 16
TOP_ROW_GAP_REM = 8 / 16

SELECT_SHADOW_COLOR = "#101820"
GLOW_SPREAD_REM = 4 / 16


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
