STATUS_DANGER = "danger"
STATUS_SUCCESS = "success"

BASE_CARD_WIDTH = 463
BASE_CARD_HEIGHT = 61
CORNER_RADIUS_RATIO = 16 / 61

BASE_PADDING = 3
BASE_ICON_SIZE = 24
BASE_ICON_GAP = 8
BASE_META_GAP = 8
GLOW_SPREAD = 12

SCALE_MIN = 0.6
SCALE_MAX = 1.5


def format_gb(size_bytes: int) -> str:
    gb = size_bytes / (1024**3)
    rounded = round(gb, 1)
    if rounded == int(rounded):
        return f"{int(rounded)}GB"
    return f"{rounded}GB"
