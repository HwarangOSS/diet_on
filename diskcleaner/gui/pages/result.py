from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from diskcleaner.gui.components.loading import icons as loading_icons
from diskcleaner.gui.components.status_card import STATUS_DANGER, STATUS_SUCCESS, StatusCard
from diskcleaner.gui.components.status_card.styles import format_gb
from diskcleaner.gui.typo import body_md, body_mini, headline, headline_small, rem, set_global_scale

# rem 단위(1rem=16px)
SUMMARY_ICON_SIZE_REM = 120 / 16
PAGE_MARGIN_REM = 20 / 16
PAGE_GAP_REM = 16 / 16
SUMMARY_GAP_REM = 20 / 16
SUMMARY_TEXT_GAP_REM = 4 / 16
HEADING_GAP_REM = 8 / 16
CARDS_GAP_REM = 4 / 16
CARDS_ITEM_GAP_REM = 12 / 16

CATEGORY_DELETE_TARGET = "delete_target"
CATEGORY_DUPLICATE = "duplicate"

# "즉시 삭제 가능"(규칙 기반, LLM 미개입) 파일도 이 카드에 합산되므로 "AI가"라고
# 단정하지 않음 - 상세화면에 들어가면 카테고리별로 구분해서 보여줌.
CARD_TEXTS = {
    CATEGORY_DELETE_TARGET: {
        "found": "삭제가 필요한 파일을 발견했어요",
        "empty": "삭제할 파일을 발견하지 못했어요",
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
        self.capacity_label.setFont(body_md())
        summary_text_col.addWidget(self.capacity_label)

        self.gb_label = QLabel("0GB")
        self.gb_label.setObjectName("resultGbLabel")
        self.gb_label.setFont(headline())
        summary_text_col.addWidget(self.gb_label)

        summary_row.addLayout(summary_text_col)
        summary_row.addStretch()

        layout.addLayout(summary_row)
        layout.addSpacing(0)
        self._heading_gap = layout.itemAt(layout.count() - 1).spacerItem()

        self.heading_label = QLabel("Result")
        self.heading_label.setObjectName("resultHeading")
        self.heading_label.setFont(headline_small())
        layout.addWidget(self.heading_label)

        self.path_label = QLabel()
        self.path_label.setObjectName("resultPathLabel")
        self.path_label.setFont(body_mini())
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

        self._apply_responsive_size()

    # API ----
    def set_path(self, path: str):
        self._scan_path = path
        self._refresh_path_text()

    def _refresh_path_text(self):
        if not self._scan_path:
            self.path_label.setText("")
            return
        metrics = QFontMetrics(self.path_label.font())
        available_width = max(self.width() - 40, 0)
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

    def _apply_responsive_size(self):
        margin = rem(PAGE_MARGIN_REM)
        self._layout.setContentsMargins(margin, margin, margin, margin)
        self._layout.setSpacing(rem(PAGE_GAP_REM))
        self._summary_row.setSpacing(rem(SUMMARY_GAP_REM))
        self._summary_text_col.setSpacing(rem(SUMMARY_TEXT_GAP_REM))
        self._heading_gap.changeSize(
            0, rem(HEADING_GAP_REM), QSizePolicy.Minimum, QSizePolicy.Fixed
        )
        self._cards_gap.changeSize(0, rem(CARDS_GAP_REM), QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.cards_layout.setSpacing(rem(CARDS_ITEM_GAP_REM))
        self._layout.invalidate()

        icon_size = rem(SUMMARY_ICON_SIZE_REM)
        if icon_size != self.summary_icon.width():
            self.summary_icon.setFixedSize(icon_size, icon_size)
            self.summary_icon.setPixmap(loading_icons.make_file1_icon(size=icon_size))

    def update_responsive_size(self, container_width: int):
        set_global_scale(container_width)
        self._apply_responsive_size()

        for card in self._cards.values():
            card.update_responsive_size(container_width)

    def refresh_fonts(self):
        self.capacity_label.setFont(body_md())
        self.gb_label.setFont(headline())
        self.heading_label.setFont(headline_small())
        self.path_label.setFont(body_mini())
        self._refresh_path_text()
        for card in self._cards.values():
            card.refresh_fonts()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_responsive_size(self.width())
        self._refresh_path_text()
