from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QScrollArea, QWidget)
from PySide6.QtCore import Qt
from database.session import Session
from models.inventory import Supplier, Movement, MovementItem, Item
from sqlalchemy import func
from utils.translation_manager import tr, tr_manager

class SupplierDetailsDialog(QDialog):
    def __init__(self, supplier_id, parent=None):
        super().__init__(parent)
        self.supplier_id = supplier_id
        self.db = Session()
        self.setWindowTitle(tr("view_analysis"))
        self.resize(1000, 700)
        self.setLayoutDirection(Qt.RightToLeft if tr_manager.is_rtl else Qt.LeftToRight)
        self.setup_ui()
        self.load_analysis()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # Stats Header
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background-color: #1c1e26; border-radius: 10px; padding: 15px;")
        stats_layout = QHBoxLayout(stats_frame)

        self.first_txn = QLabel("N/A")
        self.last_txn = QLabel("N/A")
        self.total_vol = QLabel("0.00")

        def add_stat(label, val_label):
            v = QVBoxLayout()
            l = QLabel(label)
            l.setStyleSheet("color: #7f8c8d; font-size: 11px;")
            val_label.setStyleSheet("color: #d4af37; font-size: 18px; font-weight: bold;")
            v.addWidget(l)
            v.addWidget(val_label)
            stats_layout.addLayout(v)
            stats_layout.addStretch()

        add_stat(tr("first_transaction"), self.first_txn)
        add_stat(tr("last_transaction"), self.last_txn)
        add_stat(tr("total_business_volume"), self.total_vol)

        self.main_layout.addWidget(stats_frame)

        # Items Table
        self.main_layout.addWidget(QLabel(tr("provided_items") + ":"))
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([tr("item_code"), tr("item_name"), tr("current_stock"), tr("total_value")])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.main_layout.addWidget(self.table)

    def load_analysis(self):
        # 1. Date range
        dates = self.db.query(func.min(Movement.date), func.max(Movement.date)).filter(Movement.supplier_id == self.supplier_id).first()
        if dates and dates[0]:
            self.first_txn.setText(str(dates[0]).split(' ')[0])
            self.last_txn.setText(str(dates[1]).split(' ')[0])

        # 2. Total Volume
        total = self.db.query(func.sum(Movement.final_total)).filter(Movement.supplier_id == self.supplier_id).scalar() or 0
        self.total_vol.setText(f"${float(total):,.2f}")

        # 3. Items list
        items = self.db.query(
            Item.code, Item.name, func.sum(MovementItem.quantity), func.sum(MovementItem.quantity * MovementItem.price)
        ).join(MovementItem).join(Movement).filter(Movement.supplier_id == self.supplier_id).group_by(Item.code, Item.name).all()

        self.table.setRowCount(0)
        for i in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(i[0])))
            self.table.setItem(row, 1, QTableWidgetItem(str(i[1])))
            self.table.setItem(row, 2, QTableWidgetItem(f"{float(i[2]):,.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"${float(i[3]):,.2f}"))

    def closeEvent(self, event):
        Session.remove()
        event.accept()
