from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from diskcleaner.gui.components.loading import icons as loading_icons
from diskcleaner.gui.components.status_card import STATUS_DANGER, STATUS_SUCCESS, StatusCard
from diskcleaner.gui.components.status_card.styles import format_gb
from diskcleaner.gui.typo import FontFamily, get_font

# 디자인 기준 너비. 아래 REF_* 값은 전부 "창 너비가 이만큼일 때" 실측 px이고,
# 실제로는 design_scale = 창너비 / REFERENCE_WIDTH 만큼 곱해서 쓴다. 즉 창이
# 커지거나 작아져도 항상 이 비율(margin:content:icon 등의 관계)이 그대로 유지된다.
REFERENCE_WIDTH = 880

REF_MARGIN = 190
REF_MARGIN_TOP = 150
REF_ICON_SIZE = 148
REF_SUMMARY_GAP = 20
REF_SUMMARY_TEXT_GAP = 0
REF_HEADING_GAP = 16
REF_CARDS_GAP = 8
REF_CARDS_ITEM_GAP = 16


def _design_scale(container_width: int) -> float:
    return container_width / REFERENCE_WIDTH


def _capacity_font(scale: float):
    return get_font(FontFamily.PRETENDARD_REGULAR, 14, role="body_md", scale=scale)


def _gb_font(scale: float):
    return get_font(FontFamily.PLAY_REGULAR, 26, role="headline", scale=scale)


def _heading_font(scale: float):
    return get_font(FontFamily.PLAY_REGULAR, 20, role="headline_small", scale=scale)


def _path_font(scale: float):
    return get_font(FontFamily.PRETENDARD_REGULAR, 9, role="body_mini", scale=scale)


def _tighten(label: QLabel):
    """폰트 자체의 줄간격(leading)까지 라벨 높이에 포함되는 걸 없애서, 위아래로
    쌓인 라벨끼리 spacing=0이어도 실제로 붙어 보이게 함. (음수 spacing은 창이
    커지면 값도 같이 커져서 텍스트끼리 겹쳐버리므로 쓰지 않음)"""
    metrics = QFontMetrics(label.font())
    label.setFixedHeight(metrics.ascent() + metrics.descent())


CATEGORY_DELETE_TARGET = "delete_target"
CATEGORY_DUPLICATE = "duplicate"

CARD_TEXTS = {
    CATEGORY_DELETE_TARGET: {
        "found": "AI가 삭제가 필요한 파일을 발견했어요",
        "empty": "AI가 삭제할 파일을 발견하지 못했어요",
    },
    CATEGORY_DUPLICATE: {
        "found": "AI가 중복 파일을 발견했어요",
        "empty": "AI가 중복 파일을 발견하지 못했어요",
    },
}


class ResultPage(QWidget):
    """분석 결과 요약 화면 - 삭제 대상/중복 카드, 클릭 시 상세 페이지로 이동."""

    card_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("resultPage")

        self._scan_path = ""

        self._layout = layout = QVBoxLayout(self)

        self._summary_row = summary_row = QHBoxLayout()

        self.summary_icon = QLabel()
        summary_row.addWidget(self.summary_icon, alignment=Qt.AlignVCenter)

        self._summary_text_col = summary_text_col = QVBoxLayout()

        self.capacity_label = QLabel("확보 가능 용량")
        self.capacity_label.setObjectName("resultCapacityLabel")
        summary_text_col.addWidget(self.capacity_label)

        self.gb_label = QLabel("0GB")
        self.gb_label.setObjectName("resultGbLabel")
        summary_text_col.addWidget(self.gb_label)

        summary_row.addLayout(summary_text_col)
        summary_row.setAlignment(summary_text_col, Qt.AlignVCenter)
        summary_row.addStretch()

        layout.addLayout(summary_row)
        layout.addSpacing(0)
        self._heading_gap = layout.itemAt(layout.count() - 1).spacerItem()

        self.heading_label = QLabel("Result")
        self.heading_label.setObjectName("resultHeading")
        layout.addWidget(self.heading_label)

        self.path_label = QLabel()
        self.path_label.setObjectName("resultPathLabel")
        layout.addWidget(self.path_label)

        layout.addSpacing(0)
        self._cards_gap = layout.itemAt(layout.count() - 1).spacerItem()

        self.cards_layout = QVBoxLayout()
        layout.addLayout(self.cards_layout)
        layout.addStretch()

        self._cards: dict[str, StatusCard] = {}
        for key in CARD_TEXTS:
            card = StatusCard()
            card.clicked.connect(lambda k=key: self.card_clicked.emit(k))
            self.cards_layout.addWidget(card)
            self._cards[key] = card

        self.update_responsive_size(REFERENCE_WIDTH)

    # API ----
    def set_path(self, path: str):
        self._scan_path = path
        self._refresh_path_text()

    def _refresh_path_text(self):
        if not self._scan_path:
            self.path_label.setText("")
            return
        metrics = QFontMetrics(self.path_label.font())
        margin = round(REF_MARGIN * _design_scale(self.width()))
        available_width = max(self.width() - margin * 2, 0)
        elided = metrics.elidedText(
            f"검사 대상: {self._scan_path}", Qt.ElideMiddle, available_width
        )
        self.path_label.setText(elided)

    def set_results(self, results: dict):
        total_bytes = 0
        for key, card in self._cards.items():
            data = results.get(key, {"count": 0, "size_bytes": 0})
            count = data.get("count", 0)
            size_bytes = data.get("size_bytes", 0)
            total_bytes += size_bytes

            status = STATUS_DANGER if count > 0 else STATUS_SUCCESS
            texts = CARD_TEXTS[key]
            message = texts["found"] if count > 0 else texts["empty"]
            card.set_result(status, message, count, size_bytes)

        self.gb_label.setText(format_gb(total_bytes))

    def apply_theme(self, dark: bool):
        for card in self._cards.values():
            card.set_dark(dark)

    def update_responsive_size(self, container_width: int):
        scale = _design_scale(container_width)

        self.capacity_label.setFont(_capacity_font(scale))
        self.gb_label.setFont(_gb_font(scale))
        self.heading_label.setFont(_heading_font(scale))
        self.path_label.setFont(_path_font(scale))
        _tighten(self.capacity_label)
        _tighten(self.gb_label)

        margin = round(REF_MARGIN * scale)
        margin_top = round(REF_MARGIN_TOP * scale)
        self._layout.setContentsMargins(margin, margin_top, margin, margin)
        self._layout.setSpacing(round(REF_CARDS_GAP * scale))
        self._summary_row.setSpacing(round(REF_SUMMARY_GAP * scale))
        self._summary_text_col.setSpacing(round(REF_SUMMARY_TEXT_GAP * scale))
        self._heading_gap.changeSize(
            0, round(REF_HEADING_GAP * scale), QSizePolicy.Minimum, QSizePolicy.Fixed
        )
        self._cards_gap.changeSize(
            0, round(REF_CARDS_GAP * scale), QSizePolicy.Minimum, QSizePolicy.Fixed
        )
        self.cards_layout.setSpacing(round(REF_CARDS_ITEM_GAP * scale))
        self._layout.invalidate()

        icon_size = max(1, round(REF_ICON_SIZE * scale))
        if icon_size != self.summary_icon.width():
            self.summary_icon.setFixedSize(icon_size, icon_size)
            self.summary_icon.setPixmap(loading_icons.make_file2_icon(size=icon_size))

        for card in self._cards.values():
            card.update_responsive_size(container_width)

        self._refresh_path_text()

    def refresh_fonts(self):
        self.update_responsive_size(self.width())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_responsive_size(self.width())
