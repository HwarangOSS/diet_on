STATUS_DANGER = "danger"
STATUS_SUCCESS = "success"

# 아래 REF_* 값은 result.py와 같은 기준(창 너비 1000px일 때 실측 px)이고, 실제로는
# result.py가 넘겨주는 design_scale(= 창너비 / 1000)만큼 곱해서 쓴다.
REF_CARD_HEIGHT = 84
CORNER_RADIUS_RATIO = 16 / 61  # 높이에 대한 비율이라 스케일 대상이 아님

REF_PADDING = 14
REF_ICON_SIZE = 26
REF_ICON_GAP = 12
REF_META_GAP = 10
REF_GLOW_SPREAD = 5
REF_GLOW_BLUR_RADIUS = 8


def format_gb(size_bytes: int) -> str:
    gb = size_bytes / (1024**3)
    rounded = round(gb, 1)
    if rounded == int(rounded):
        return f"{int(rounded)}GB"
    return f"{rounded}GB"
