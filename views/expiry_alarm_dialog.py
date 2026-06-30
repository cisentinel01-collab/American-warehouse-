from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QGroupBox, QGridLayout, QPushButton, QHBoxLayout)
from PySide6.QtCore import Qt

class ExpiryAlarmDialog(QDialog):
    def __init__(self, expired, soon, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تنبيه انتهاء الصلاحية")
        self.resize(600, 400)
        self.setLayoutDirection(Qt.RightToLeft)

        layout = QVBoxLayout(self)

        if expired:
            exp_group = QGroupBox("أصناف منتهية الصلاحية")
            exp_layout = QVBoxLayout(exp_group)
            for item in expired:
                l = QLabel(f"• {item.item.name} ({item.lot_number}) - انتهى في: {item.expiry_date}")
                l.setStyleSheet("color: #e74c3c; font-weight: bold;")
                exp_layout.addWidget(l)
            layout.addWidget(exp_group)

        if soon:
            soon_group = QGroupBox("أصناف تنتهي قريباً (خلال 6 أشهر)")
            soon_layout = QVBoxLayout(soon_group)
            for item in soon:
                l = QLabel(f"• {item.item.name} ({item.lot_number}) - ينتهي في: {item.expiry_date}")
                l.setStyleSheet("color: #f39c12;")
                soon_layout.addWidget(l)
            layout.addWidget(soon_group)

        btn_layout = QHBoxLayout()
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
