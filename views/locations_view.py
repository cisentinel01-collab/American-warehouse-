from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QLineEdit, QLabel,
                             QHeaderView, QComboBox, QMessageBox)
from PySide6.QtCore import Qt
import qtawesome as qta
from database.session import Session
from models.inventory import Location

class LocationsView(QWidget):
    def __init__(self):
        super().__init__()
        # Every view should use a local scoped session or the global scoped session object
        self.db = Session()
        self.setup_ui()

    def setup_ui(self):
        from utils.translation_manager import tr, tr_manager
        self.setLayoutDirection(Qt.RightToLeft if tr_manager.is_rtl else Qt.LeftToRight)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Toolbar
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("search"))
        self.search_input.textChanged.connect(self.refresh)
        toolbar.addWidget(self.search_input)

        add_btn = QPushButton(tr("add_location"))
        add_btn.setObjectName("PrimaryButton")
        add_btn.setIcon(qta.icon("fa5s.plus", color="white"))
        add_btn.clicked.connect(self.show_add_dialog)
        toolbar.addWidget(add_btn)

        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([tr("id"), tr("location_name"), tr("description"), tr("actions")])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        try:
            term = self.search_input.text()
            query = self.db.query(Location).filter(Location.active == True)
            if term:
                query = query.filter(Location.name.ilike(f"%{term}%"))

            locations = query.all()

            self.table.setRowCount(0)
            for loc in locations:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(loc.id)))
                self.table.setItem(row, 1, QTableWidgetItem(str(loc.name)))
                self.table.setItem(row, 2, QTableWidgetItem(str(loc.description or "")))

                del_btn = QPushButton()
                del_btn.setIcon(qta.icon("fa5s.trash-alt", color="white"))
                del_btn.setFixedSize(30, 30)
                del_btn.setStyleSheet("background-color: #e74c3c; border-radius: 5px;")
                del_btn.clicked.connect(lambda _, l=loc: self.handle_delete(l))
                self.table.setCellWidget(row, 3, del_btn)
        except Exception as e:
            from app_logging.app_logger import app_logger
            app_logger.error(f"LocationsView refresh error: {e}")
            self.db.rollback()

    def handle_delete(self, loc):
        if QMessageBox.question(self, "تأكيد", f"حذف الموقع '{loc.name}'؟") == QMessageBox.Yes:
            try:
                loc.active = False
                self.db.commit()
                self.refresh()
            except Exception as e:
                self.db.rollback()
                QMessageBox.critical(self, "خطأ", f"فشل الحذف: {str(e)}")

    def show_add_dialog(self):
        from PySide6.QtWidgets import QDialog, QFormLayout
        from utils.translation_manager import tr, tr_manager
        dialog = QDialog(self)
        dialog.setLayoutDirection(Qt.RightToLeft if tr_manager.is_rtl else Qt.LeftToRight)
        dialog.setWindowTitle(tr("add_location"))
        d_layout = QFormLayout(dialog)
        d_layout.setLabelAlignment(Qt.AlignRight if tr_manager.is_rtl else Qt.AlignLeft)

        name_input = QLineEdit()
        desc_input = QLineEdit()

        d_layout.addRow(tr("location_name") + ":", name_input)
        d_layout.addRow(tr("description") + ":", desc_input)

        save_btn = QPushButton(tr("save"))
        save_btn.setObjectName("GoldButton")
        save_btn.clicked.connect(lambda: self.save_location(dialog, name_input.text(), desc_input.text()))
        d_layout.addRow(save_btn)

        dialog.exec()

    def save_location(self, dialog, name, desc):
        if not name:
            QMessageBox.warning(self, "تنبيه", "الاسم مطلوب")
            return

        try:
            new_loc = Location(name=name, description=desc)
            self.db.add(new_loc)
            self.db.commit()
            dialog.accept()
            self.refresh()
        except Exception as e:
            self.db.rollback()
            QMessageBox.critical(self, "خطأ", f"فشل الحفظ: {str(e)}")

    def closeEvent(self, event):
        from database.session import Session
        Session.remove()
        event.accept()
