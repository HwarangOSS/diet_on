from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from diskcleaner.gui.components.loading import icons as loading_icons
from diskcleaner.gui.components.status_card import STATUS_DANGER, STATUS_SUCCESS, StatusCard
from diskcleaner.gui.components.status_card.styles import format_gb
from diskcleaner.gui.typo import body_md, headline, headline_small

SUMMARY_ICON_SIZE = 120

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
    card_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("resultPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        summary_row = QHBoxLayout()
        summary_row.setSpacing(20)

        self.summary_icon = QLabel()
        self.summary_icon.setFixedSize(SUMMARY_ICON_SIZE, SUMMARY_ICON_SIZE)
        self.summary_icon.setPixmap(loading_icons.make_file1_icon(size=SUMMARY_ICON_SIZE))
        summary_row.addWidget(self.summary_icon, alignment=Qt.AlignVCenter)

        summary_text_col = QVBoxLayout()
        summary_text_col.setSpacing(4)

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
        layout.addSpacing(8)

        self.heading_label = QLabel("Result")
        self.heading_label.setObjectName("resultHeading")
        self.heading_label.setFont(headline_small())
        layout.addWidget(self.heading_label)

        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(12)
        layout.addLayout(self.cards_layout)
        layout.addStretch()

        self._cards: dict[str, StatusCard] = {}
        for key in CARD_TEXTS:
            card = StatusCard()
            card.clicked.connect(lambda k=key: self.card_clicked.emit(k))
            self.cards_layout.addWidget(card)
            self._cards[key] = card

    # API ----
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
        for card in self._cards.values():
            card.update_responsive_size(container_width)

    def refresh_fonts(self):
        self.capacity_label.setFont(body_md())
        self.gb_label.setFont(headline())
        self.heading_label.setFont(headline_small())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_responsive_size(self.width())
