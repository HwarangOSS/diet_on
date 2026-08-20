from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from diskcleaner.gui.components.loading import icons as loading_icons
from diskcleaner.gui.components.side_action_button import SideActionButton
from diskcleaner.gui.typo import headline, rem

from . import styles

TITLE_TEXT = "Delete Complete!"
RESULT_BUTTON_TEXT = "Result"


class CompletePage(QWidget):
    result_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("completePage")

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.result_button = SideActionButton()
        self.result_button.set_text(RESULT_BUTTON_TEXT)
        self.result_button.clicked.connect(self.result_requested.emit)
        outer.addWidget(self.result_button, alignment=Qt.AlignVCenter)

        self._layout = layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(0)
        outer.addLayout(layout, stretch=1)

        self._right_spacer = QWidget()
        outer.addWidget(self._right_spacer)

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

        self._apply_responsive_size(styles.REFERENCE_WIDTH)

    def apply_theme(self, dark: bool):
        self.result_button.set_dark(dark)

    def _apply_responsive_size(self, container_width: int):
        self._icon_gap.changeSize(
            0, rem(styles.ICON_GAP_REM), QSizePolicy.Minimum, QSizePolicy.Fixed
        )
        self._layout.invalidate()

        icon_size = rem(styles.ICON_SIZE_REM)
        if icon_size != self.icon_label.width():
            self.icon_label.setFixedSize(icon_size, icon_size)
            self.icon_label.setPixmap(loading_icons.make_file1_icon(size=icon_size))

        scale = container_width / styles.REFERENCE_WIDTH
        self.result_button.update_responsive_size(self.height(), scale=scale)
        self._right_spacer.setFixedWidth(self.result_button.width())

    def update_responsive_size(self, container_width: int):
        self._apply_responsive_size(container_width)

    def refresh_fonts(self):
        self.title_label.setFont(headline())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_responsive_size(self.width())
