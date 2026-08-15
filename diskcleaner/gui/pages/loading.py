from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel, QSizePolicy, QVBoxLayout, QWidget

from diskcleaner.gui.components.loading import icons
from diskcleaner.gui.components.loading.progress_bar import LoadingProgressBar
from diskcleaner.gui.typo import body_md, body_mini, headline, rem

LOADING_MESSAGES = [
    "AI가 파일을 탐색 중이에요",
    "삭제할 파일을 찾는 중이에요",
    "중복 파일을 분석 중이에요",
    "불필요한 파일을 정리하고 있어요",
    "거의 다 됐어요, 조금만 기다려주세요",
]

ICON_SWAP_INTERVAL_MS = 600
MESSAGE_INTERVAL_MS = 2200
FADE_DURATION_MS = 350

# rem 단위(1rem=16px)
ICON_SIZE_REM = icons.ICON_SIZE / 16
ICON_GAP_REM = 20 / 16
TITLE_GAP_REM = 8 / 16
PATH_GAP_REM = 8 / 16
PROGRESS_GAP_REM = 16 / 16


class LoadingPage(QWidget):
    """분석 진행 중 화면 - 진행률 표시와 안내 메시지 로테이션."""

    analyze_finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("loadingPage")

        self._is_dark = False
        self._icon_toggle = False
        self._message_index = 0
        self._scan_path = ""

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(0)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)

        layout.addSpacing(0)
        self._icon_gap = layout.itemAt(layout.count() - 1).spacerItem()

        self.title_label = QLabel("Finding...")
        self.title_label.setObjectName("loadingTitle")
        self.title_label.setFont(headline())
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        layout.addSpacing(0)
        self._title_gap = layout.itemAt(layout.count() - 1).spacerItem()

        self.message_label = QLabel(LOADING_MESSAGES[0])
        self.message_label.setObjectName("loadingMessage")
        self.message_label.setFont(body_md())
        self.message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.message_label)

        self._message_opacity = QGraphicsOpacityEffect(self.message_label)
        self.message_label.setGraphicsEffect(self._message_opacity)
        self._message_opacity.setOpacity(1.0)

        layout.addSpacing(0)
        self._path_gap = layout.itemAt(layout.count() - 1).spacerItem()

        self.path_label = QLabel()
        self.path_label.setObjectName("loadingPathLabel")
        self.path_label.setFont(body_mini())
        self.path_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.path_label)

        layout.addSpacing(0)
        self._progress_gap = layout.itemAt(layout.count() - 1).spacerItem()

        self.progress_bar = LoadingProgressBar()
        layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)

        self._icon_timer = QTimer(self)
        self._icon_timer.timeout.connect(self._toggle_icon)

        self._message_timer = QTimer(self)
        self._message_timer.timeout.connect(self._next_message)

        self._apply_responsive_size()

    def set_path(self, path: str):
        self._scan_path = path
        self._refresh_path_text()

    def _refresh_path_text(self):
        if not self._scan_path:
            self.path_label.setText("")
            return
        metrics = QFontMetrics(self.path_label.font())
        available_width = max(self.width() - 40, 0)
        elided = metrics.elidedText(f"검사 대상: {self._scan_path}", Qt.ElideMiddle, available_width)
        self.path_label.setText(elided)

    def _apply_responsive_size(self):
        self._icon_gap.changeSize(0, rem(ICON_GAP_REM), QSizePolicy.Minimum, QSizePolicy.Fixed)
        self._title_gap.changeSize(0, rem(TITLE_GAP_REM), QSizePolicy.Minimum, QSizePolicy.Fixed)
        self._path_gap.changeSize(0, rem(PATH_GAP_REM), QSizePolicy.Minimum, QSizePolicy.Fixed)
        self._progress_gap.changeSize(
            0, rem(PROGRESS_GAP_REM), QSizePolicy.Minimum, QSizePolicy.Fixed
        )
        self.layout().invalidate()
        self.progress_bar.update_responsive_size()
        self._apply_icon()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_path_text()

    def start(self):
        self._icon_timer.start(ICON_SWAP_INTERVAL_MS)
        self._message_timer.start(MESSAGE_INTERVAL_MS)

    def stop(self):
        self._icon_timer.stop()
        self._message_timer.stop()

    def update_progress(self, value: float):
        self.progress_bar.set_progress(value)
        if value >= 100:
            self.analyze_finished.emit()

    def _toggle_icon(self):
        self._icon_toggle = not self._icon_toggle
        self._apply_icon()

    def _apply_icon(self):
        icon_size = rem(ICON_SIZE_REM)
        self.icon_label.setFixedSize(icon_size, icon_size)
        pixmap = (
            icons.make_file2_icon(size=icon_size)
            if self._icon_toggle
            else icons.make_file1_icon(size=icon_size)
        )
        self.icon_label.setPixmap(pixmap)

    def _next_message(self):
        self._message_index = (self._message_index + 1) % len(LOADING_MESSAGES)
        next_text = LOADING_MESSAGES[self._message_index]

        fade_out = QPropertyAnimation(self._message_opacity, b"opacity")
        fade_out.setDuration(FADE_DURATION_MS)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.InCubic)

        def on_fade_out_finished():
            self.message_label.setText(next_text)
            fade_in = QPropertyAnimation(self._message_opacity, b"opacity")
            fade_in.setDuration(FADE_DURATION_MS)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.OutCubic)
            fade_in.start()
            self._current_anim = fade_in

        fade_out.finished.connect(on_fade_out_finished)
        fade_out.start()
        self._current_anim = fade_out

    def apply_theme(self, dark: bool):
        self._is_dark = dark
        self.progress_bar.set_dark(dark)

    def refresh_fonts(self):
        self.title_label.setFont(headline())
        self.message_label.setFont(body_md())
        self.path_label.setFont(body_mini())
        self._apply_responsive_size()
        self._refresh_path_text()
