"""A simple read-only table model for showing result rows."""

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class TableModel(QAbstractTableModel):
    """Shows a list of rows. Floats are shown with 4 decimals; sorting uses the raw values."""

    def __init__(self, columns, rows=None, parent=None):
        super().__init__(parent)
        self._columns = list(columns)
        self._rows = rows or []

    def set_rows(self, rows):
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._columns[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        value = self._rows[index.row()][index.column()]
        if role == Qt.DisplayRole:
            return f"{value:.4f}" if isinstance(value, float) else str(value)
        if role == Qt.UserRole:  # used for sorting
            return value
        if role == Qt.TextAlignmentRole and isinstance(value, (int, float)):
            return int(Qt.AlignRight | Qt.AlignVCenter)
        return None
