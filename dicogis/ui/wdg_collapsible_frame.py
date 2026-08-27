#! python3  # noqa: E265


"""
Name:         Custom collapsible frame
Purpose:      Allow toggle a frame in pure Python Qt.

Author:       Julien Moura (@geojulien)
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from pathlib import Path

# 3rd party
from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget

# project
from dicogis.utils.utils import Utilities

# ##############################################################################
# ############ Globals ############
# #################################

logger = logging.getLogger(__name__)


# ##############################################################################
# ########## Classes ###############
# ##################################


class ToggledFrame(QWidget):
    """A frame that can be toggled to open and close."""

    def __init__(
        self,
        parent: QWidget | None = None,
        in_text: str = "",
        start_opened: bool = True,
        **kwargs,
    ):
        """Initializes a collapsible frame.

        Args:
            parent: Qt parent widget.
            in_text: text to display next to the toggle arrow. Defaults to empty
                string.
            start_opened: whether the frame is expanded on creation. Defaults to
                True.
            kwargs: unused, kept for backward-compatibility with the previous
                signature.
        """
        super().__init__(parent)
        uic.loadUi(
            Utilities().resolve_internal_path(
                internal_path=Path("ui/wdg_collapsible_frame.ui")
            ),
            self,
        )

        self.btn_toggle.setText(in_text)
        self.btn_toggle.setChecked(start_opened)
        self.btn_toggle.setArrowType(
            Qt.ArrowType.DownArrow if start_opened else Qt.ArrowType.RightArrow
        )
        self.sub_frame.setVisible(start_opened)
        self.btn_toggle.toggled.connect(self._on_toggled)

    def _on_toggled(self, checked: bool) -> None:
        """Show/hide the sub frame and update the toggle arrow.

        Args:
            checked: whether the frame should be expanded.
        """
        self.sub_frame.setVisible(checked)
        self.btn_toggle.setArrowType(
            Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow
        )

    def toggle(self) -> None:
        """Toggle opened or closed."""
        self.btn_toggle.setChecked(not self.btn_toggle.isChecked())


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout

    app = QApplication(sys.argv)

    window = QWidget()
    window_layout = QVBoxLayout(window)

    collapsible_frame = ToggledFrame(parent=window, in_text="Rotate", start_opened=True)
    inner_layout = QVBoxLayout(collapsible_frame.sub_frame)
    button = QPushButton("Close window")
    button.clicked.connect(window.close)
    inner_layout.addWidget(button)

    window_layout.addWidget(collapsible_frame)
    window.show()
    sys.exit(app.exec())
