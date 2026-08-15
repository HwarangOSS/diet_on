STATUS_DANGER = "danger"
STATUS_SUCCESS = "success"

# rem 단위(1rem=16px)
CARD_WIDTH_REM = 463 / 16
CARD_HEIGHT_REM = 61 / 16
CORNER_RADIUS_RATIO = 16 / 61  # 높이에 대한 비율이라 px 변환 대상이 아님

PADDING_REM = 3 / 16
ICON_SIZE_REM = 24 / 16
ICON_GAP_REM = 8 / 16
META_GAP_REM = 8 / 16
GLOW_SPREAD_REM = 12 / 16
GLOW_BLUR_RADIUS_REM = 8 / 16


def format_gb(size_bytes: int) -> str:
    gb = size_bytes / (1024**3)
    rounded = round(gb, 1)
    if rounded == int(rounded):
        return f"{int(rounded)}GB"
    return f"{rounded}GB"
