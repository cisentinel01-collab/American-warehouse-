from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from typing import List, Any, Dict

class EnterpriseTableModel(QAbstractTableModel):
    def __init__(self, data: List[Dict[str, Any]], headers: List[str], translated_headers: List[str] = None, parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = headers
        self._translated_headers = translated_headers or headers

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None

        row_data = self._data[index.row()]
        key = self._headers[index.column()]

        if role == Qt.DisplayRole:
            val = row_data.get(key, "")
            # Enhanced Formatting: Money and Numbers
            if any(x in key.lower() for x in ['total', 'price', 'balance', 'debit', 'credit', 'amount']):
                try:
                    return f"{float(val):,.2f}"
                except: pass
            return str(val)

        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

        if role == Qt.ForegroundRole:
            # Color coding for status and movement types
            val_str = str(row_data.get(key, "")).upper()
            if val_str in ["IN", "ACTIVE", "POSTED", "SUCCESS", "TRUE"]:
                from PySide6.QtGui import QColor
                return QColor("#27ae60")
            if val_str in ["OUT", "DEACTIVATED", "CANCELLED", "ERROR", "FALSE"]:
                from PySide6.QtGui import QColor
                return QColor("#e74c3c")

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section < len(self._translated_headers):
                return self._translated_headers[section]
            return self._headers[section]
        return None

    def update_data(self, new_data: List[Dict[str, Any]]):
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()
