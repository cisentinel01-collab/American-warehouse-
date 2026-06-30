from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QLabel, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt

class ImportVerificationDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("مراجعة البيانات المستخرجة من الفاتورة")
        self.resize(800, 500)
        self.setLayoutDirection(Qt.RightToLeft)
        self.original_data = data
        self.confirmed_data = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("يرجى مراجعة وتعديل البيانات قبل استيرادها للمخزن:"))

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["الكود", "اسم الصنف", "الكمية", "السعر", "تاريخ الانتاج", "تاريخ الانتهاء"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.load_data()
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        confirm_btn = QPushButton("تأكيد الاستيراد")
        confirm_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-weight: bold;")
        confirm_btn.clicked.connect(self.accept_data)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(confirm_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def load_data(self):
        self.table.setRowCount(0)
        for item in self.original_data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get('code', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get('name', ''))))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get('quantity', 0))))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get('price', 0))))
            self.table.setItem(row, 4, QTableWidgetItem(str(item.get('production_date', ''))))
            self.table.setItem(row, 5, QTableWidgetItem(str(item.get('expiry_date', ''))))

    def accept_data(self):
        self.confirmed_data = []
        for row in range(self.table.rowCount()):
            try:
                code_item = self.table.item(row, 0)
                name_item = self.table.item(row, 1)
                qty_item = self.table.item(row, 2)
                price_item = self.table.item(row, 3)

                if not code_item or not name_item or not qty_item or not price_item:
                    continue

                self.confirmed_data.append({
                    'code': code_item.text(),
                    'name': name_item.text(),
                    'quantity': float(qty_item.text()),
                    'price': float(price_item.text()),
                    'production_date': self.table.item(row, 4).text() if self.table.item(row, 4) else None,
                    'expiry_date': self.table.item(row, 5).text() if self.table.item(row, 5) else None
                })
            except ValueError:
                QMessageBox.warning(self, "خطأ", f"خطأ في بيانات الصف رقم {row+1}")
                return
        self.accept()
