from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableView,
                             QPushButton, QLineEdit, QLabel,
                             QHeaderView, QGroupBox, QDialog, QFormLayout, QComboBox, QMessageBox)
from PySide6.QtCore import Qt, QThreadPool
import qtawesome as qta
from utils.auth import AuthManager
from views_components.enterprise_table_model import EnterpriseTableModel
from workers.worker import Worker
from database.session import Session

class UserManagementView(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.threadpool = QThreadPool()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        toolbar = QHBoxLayout()
        add_btn = QPushButton("إضافة مستخدم جديد")
        add_btn.setObjectName("GoldButton")
        add_btn.setIcon(qta.icon("fa5s.user-plus", color="black"))
        add_btn.clicked.connect(self.show_add_dialog)
        toolbar.addWidget(add_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.view = QTableView()
        self.view.setEditTriggers(QTableView.NoEditTriggers)
        self.view.setSelectionBehavior(QTableView.SelectRows)
        self.view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.view)

        self.headers = ["full_name", "username", "role", "is_active"]
        self.model = EnterpriseTableModel([], self.headers)
        self.view.setModel(self.model)

        self.refresh()

    def refresh(self):
        worker = Worker(self.controller.get_all_users)
        worker.signals.result.connect(self.on_data_loaded)
        self.threadpool.start(worker)

    def on_data_loaded(self, users):
        data = [
            {
                "id": u.id, "full_name": u.full_name, "username": u.username,
                "role": u.role, "is_active": "نشط" if u.is_active else "معطل"
            }
            for u in users
        ]
        self.model.update_data(data)

    def show_add_dialog(self):
        from utils.validator import Validator
        dialog = QDialog(self)
        dialog.setWindowTitle("إضافة مستخدم")
        dialog.setMinimumWidth(400)
        d_layout = QFormLayout(dialog)

        full_name = QLineEdit()
        Validator.setup_strict_validation(full_name, "name")
        username = QLineEdit()
        password = QLineEdit()
        password.setEchoMode(QLineEdit.Password)
        role = QComboBox()
        role.addItem("مسؤول مخزن", "warehouse_manager")
        role.addItem("المتابعة", "follow_up")

        d_layout.addRow("الاسم الكامل:", full_name)
        d_layout.addRow("اسم المستخدم:", username)
        d_layout.addRow("كلمة المرور:", password)
        d_layout.addRow("الدور:", role)

        save = QPushButton("حفظ")
        save.setObjectName("GoldButton")
        save.clicked.connect(lambda: self.save_user(dialog, {
            "full_name": full_name.text(),
            "username": username.text(),
            "password": password.text(),
            "role": role.currentData()
        }))
        d_layout.addRow(save)
        dialog.exec()

    def save_user(self, dialog, data):
        if not data['username'] or not data['password']:
            QMessageBox.warning(self, "تنبيه", "جميع الحقول مطلوبة")
            return
        self.controller.add_user(data)
        dialog.accept()
        self.refresh()

    def handle_delete(self, user_id):
        if QMessageBox.question(self, "تأكيد", "هل أنت متأكد من تعطيل هذا المستخدم؟") == QMessageBox.Yes:
            if self.controller.delete_user(user_id):
                self.refresh()

    def closeEvent(self, event):
        Session.remove()
        event.accept()
