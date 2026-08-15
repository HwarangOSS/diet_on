from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from diskcleaner.gui.components.loading import icons as loading_icons
from diskcleaner.gui.typo import body_md, headline, rem

# rem 단위(1rem=16px)
ICON_SIZE_REM = 120 / 16
ICON_GAP_REM = 20 / 16
TITLE_GAP_REM = 8 / 16

# 가정: 목업(Complete.png)에 자동 전환 트리거가 표시되어 있지 않아,
# 로딩 화면과 비슷하게 일정 시간 뒤 자동으로 다음 화면으로 넘어가도록 구현.
# 필요 시 AUTO_CONTINUE_MS 값이나 트리거 방식(버튼 클릭 등)을 조정하면 됨.
AUTO_CONTINUE_MS = 1500

TITLE_TEXT = "Delete Complete!"


class CompletePage(QWidget):
    """실제 삭제 완료 후 결과를 알려주는 화면.

    Delete/Duplicate 상세 화면에서 삭제를 실행하면 재탐색(Loading) 대신
    이 화면으로 이동해 "삭제가 실제로 처리되었다"는 것을 명확히 보여준다.
    표시 후 일정 시간이 지나면 continue_requested 시그널을 emit하여
    호출부가 다음 화면(예: Home)으로 전환하도록 한다.
    """

    continue_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("completePage")

        self._layout = layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(0)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)

        layout.addSpacing(0)
        self._icon_gap = layout.itemAt(layout.count() - 1).spacerItem()

        self.title_label = QLabel(TITLE_TEXT)
        self.title_label.setObjectName("completeTitle")
        self.title_label.setFont(headline())
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        layout.addSpacing(0)
        self._title_gap = layout.itemAt(layout.count() - 1).spacerItem()

        # 가정: 목업에는 없지만, 몇 개를 지워서 얼마나 확보했는지 보여주는 게
        # 사용자에게 "진짜로 삭제됐다"는 확신을 주는 데 도움이 될 것 같아 추가.
        # 불필요하면 이 라벨과 set_result() 호출만 제거하면 됨.
        self.summary_label = QLabel()
        self.summary_label.setObjectName("completeSummary")
        self.summary_label.setFont(body_md())
        self.summary_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.summary_label)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.continue_requested.emit)

        self._apply_responsive_size()

    # API
    def set_result(self, deleted_count: int, size_freed_bytes: int):
        if deleted_count <= 0:
            self.summary_label.setText("")
            return
        if size_freed_bytes >= 1024**3:
            size_text = f"{size_freed_bytes / (1024 ** 3):.1f}GB"
        else:
            size_text = f"{size_freed_bytes / (1024 ** 2):.0f}MB"
        self.summary_label.setText(f"{deleted_count}개 파일 삭제 · {size_text} 확보")

    def start(self, delay_ms: int = AUTO_CONTINUE_MS):
        self._timer.start(delay_ms)

    def stop(self):
        self._timer.stop()

    def apply_theme(self, dark: bool):
        # 배경/기본 텍스트 색상은 theme.py의 전역 QSS(QWidget 셀렉터)가 처리한다.
        pass

    def _apply_responsive_size(self):
        self._icon_gap.changeSize(0, rem(ICON_GAP_REM), QSizePolicy.Minimum, QSizePolicy.Fixed)
        self._title_gap.changeSize(0, rem(TITLE_GAP_REM), QSizePolicy.Minimum, QSizePolicy.Fixed)
        self._layout.invalidate()

        icon_size = rem(ICON_SIZE_REM)
        if icon_size != self.icon_label.width():
            self.icon_label.setFixedSize(icon_size, icon_size)
            self.icon_label.setPixmap(loading_icons.make_file1_icon(size=icon_size))

    def update_responsive_size(self, container_width: int):
        self._apply_responsive_size()

    def refresh_fonts(self):
        self.title_label.setFont(headline())
        self.summary_label.setFont(body_md())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_responsive_size(self.width())
