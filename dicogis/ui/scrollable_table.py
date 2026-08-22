#! python3  # noqa: E265

from PyQt6.QtWidgets import (
    QAbstractItemView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from dicogis.utils.texts import TextsManager


class ScrollableTable(QWidget):
    """
    A scrollable table with two columns in read-only mode.

    Attributes:
        table (QTableWidget): The table widget displaying key/value rows.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        localized_strings: dict | None = None,
        init_widgets: bool = True,
    ):
        """Initialize the ScrollableTable widget.

        Args:
            parent: the parent widget.
            localized_strings: translated strings. Defaults to None.
            init_widgets: option to create widgets during init or not. Defaults to True.
        """
        super().__init__(parent)

        # handle empty localized strings
        self.localized_strings = localized_strings
        if self.localized_strings is None:
            self.localized_strings = TextsManager().load_texts()

        if init_widgets:
            self.create_widgets()

    def create_widgets(self) -> None:
        """Create and layout the widgets for the frame."""
        self.table = QTableWidget(0, 2, self)
        self.table.setHorizontalHeaderLabels(
            [
                self.localized_strings.get("key", "Key"),
                self.localized_strings.get("value", "Value"),
            ]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)

    def add_row(self, key: str, value: str) -> None:
        """Append a key/value row to the table.

        Args:
            key: value for the first column.
            value: value for the second column.
        """
        row_index = self.table.rowCount()
        self.table.insertRow(row_index)
        self.table.setItem(row_index, 0, QTableWidgetItem(str(key)))
        self.table.setItem(row_index, 1, QTableWidgetItem(str(value)))
