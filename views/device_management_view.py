from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QMessageBox,
    QAbstractItemView,
    QHeaderView
)

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from datetime import date, timedelta


class DeviceManagementView(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)

        # جدول الأجهزة
        self.table = QTableWidget()
        self.table.setColumnCount(5)

        self.table.setHorizontalHeaderLabels([
            "ID",
            "اسم الجهاز",
            "الحالة",
            "أول اتصال",
            "انتهاء الصلاحية"
        ])

        # تحسينات الجدول
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setFocusPolicy(Qt.NoFocus)

        layout.addWidget(self.table)

        # الأزرار
        buttons_layout = QHBoxLayout()

        self.activate_btn = QPushButton("تفعيل سنة")
        self.block_btn = QPushButton("حظر الجهاز")
        self.delete_btn = QPushButton("حذف الجهاز")
        self.refresh_btn = QPushButton("تحديث")

        buttons_layout.addWidget(self.activate_btn)
        buttons_layout.addWidget(self.block_btn)
        buttons_layout.addWidget(self.delete_btn)
        buttons_layout.addWidget(self.refresh_btn)

        layout.addLayout(buttons_layout)

        # ربط الأزرار
        self.activate_btn.clicked.connect(self.activate_device)
        self.block_btn.clicked.connect(self.block_device)
        self.delete_btn.clicked.connect(self.delete_device)
        self.refresh_btn.clicked.connect(self.load_data)

        self.load_data()

    def load_data(self):

        self.table.setRowCount(0)

        devices = self.controller.get_all_devices()

        self.table.setRowCount(len(devices))

        for row, device in enumerate(devices):

            self.table.setItem(row, 0, QTableWidgetItem(str(device["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(device["computer_name"]))

            status_text = device["status"]
            status_item = QTableWidgetItem(status_text)

            if status_text == "active":
                status_item.setBackground(QColor("#16a34a"))
                status_item.setForeground(QColor("white"))

            elif status_text == "pending":
                status_item.setBackground(QColor("#facc15"))

            elif status_text == "blocked":
                status_item.setBackground(QColor("#dc2626"))
                status_item.setForeground(QColor("white"))

            self.table.setItem(row, 2, status_item)

            self.table.setItem(
                row, 3,
                QTableWidgetItem(str(device["first_seen"]))
            )

            self.table.setItem(
                row, 4,
                QTableWidgetItem(str(device["expiry_date"]))
            )

    def activate_device(self):

        row = self.table.currentRow()

        if row < 0:
            QMessageBox.warning(self, "تنبيه", "اختر جهازاً أولاً")
            return

        device_id = int(self.table.item(row, 0).text())

        expiry_date = date.today() + timedelta(days=365)

        self.controller.activate_device(device_id, expiry_date)

        QMessageBox.information(self, "نجاح", "تم تفعيل الجهاز لمدة سنة")

        self.load_data()

    def block_device(self):

        row = self.table.currentRow()

        if row < 0:
            QMessageBox.warning(self, "تنبيه", "اختر جهازاً أولاً")
            return

        device_id = int(self.table.item(row, 0).text())

        self.controller.block_device(device_id)

        QMessageBox.information(self, "نجاح", "تم حظر الجهاز")

        self.load_data()

    def delete_device(self):

        row = self.table.currentRow()

        if row < 0:
            QMessageBox.warning(self, "تنبيه", "اختر جهازاً أولاً")
            return

        device_id = int(self.table.item(row, 0).text())

        reply = QMessageBox.question(
            self,
            "تأكيد",
            "هل تريد حذف الجهاز؟"
        )

        if reply == QMessageBox.Yes:
            self.controller.delete_device(device_id)
            self.load_data()
