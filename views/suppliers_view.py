from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableView,
                             QPushButton, QLineEdit, QLabel,
                             QHeaderView, QGroupBox, QMessageBox)
from PySide6.QtCore import Qt, QThreadPool
import qtawesome as qta
from utils.auth import AuthManager
from views_components.enterprise_table_model import EnterpriseTableModel
from workers.worker import Worker
from database.session import Session
from utils.signals import signal_manager

class SuppliersView(QWidget):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self.threadpool = QThreadPool()
        self.setup_ui()

    def setup_ui(self):
        from utils.translation_manager import tr
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Toolbar
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("search"))
        self.search_input.textChanged.connect(self.handle_search)
        toolbar.addWidget(self.search_input)

        add_btn = QPushButton(tr("suppliers"))
        add_btn.setObjectName("PrimaryButton")
        add_btn.setIcon(qta.icon("fa5s.plus", color="white"))
        if not AuthManager.has_permission('suppliers', 'add'):
            add_btn.setEnabled(False)

        add_btn.clicked.connect(self.show_add_dialog)
        toolbar.addWidget(add_btn)

        import_btn = QPushButton(tr("import_excel"))
        import_btn.setObjectName("SecondaryButton")
        import_btn.clicked.connect(self.handle_import)
        toolbar.addWidget(import_btn)

        layout.addLayout(toolbar)

        # Table
        self.view = QTableView()
        self.view.setEditTriggers(QTableView.NoEditTriggers)
        self.view.setSelectionBehavior(QTableView.SelectRows)
        self.view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.show_context_menu)
        self.view.doubleClicked.connect(self.handle_analysis)
        layout.addWidget(self.view)

        self.headers = ["name", "phone", "email", "address", "actions"]
        self.translated_headers = [tr("item_name"), tr("phone"), "Email", tr("address"), tr("actions")]
        self.model = EnterpriseTableModel([], self.headers, self.translated_headers)
        self.view.setModel(self.model)

        self.refresh()
        signal_manager.supplier_changed.connect(self.refresh)

    def refresh(self, suppliers=None):
        if suppliers:
            self.on_data_loaded(suppliers)
            return

        worker = Worker(self.service.get_all)
        worker.signals.result.connect(self.on_data_loaded)
        self.threadpool.start(worker)

    def on_data_loaded(self, suppliers):
        from utils.translation_manager import tr
        data = [
            {
                "id": s.id, "name": s.name, "phone": s.phone, "email": s.email, "address": s.address,
                "actions": tr("view_analysis")
            }
            for s in suppliers
        ]
        self.model.update_data(data)

    def show_context_menu(self, pos):
        from PySide6.QtWidgets import QMenu
        from utils.translation_manager import tr
        index = self.view.indexAt(pos)
        if not index.isValid(): return

        menu = QMenu(self)
        analysis_act = menu.addAction(qta.icon("fa5s.chart-bar"), tr("view_analysis"))
        edit_act = menu.addAction(qta.icon("fa5s.edit"), tr("edit"))
        delete_act = menu.addAction(qta.icon("fa5s.trash-alt"), tr("delete"))

        action = menu.exec(self.view.viewport().mapToGlobal(pos))
        if action == analysis_act:
            self.handle_analysis(index)
        elif action == edit_act:
            self.handle_edit(index)
        elif action == delete_act:
            s_id = self.model._data[index.row()].get("id")
            self.handle_delete(s_id)

    def handle_analysis(self, index):
        if not index.isValid(): return
        s_id = self.model._data[index.row()].get("id")
        if s_id:
            from views.supplier_details_dialog import SupplierDetailsDialog
            dialog = SupplierDetailsDialog(s_id, self)
            dialog.exec()

    def handle_edit(self, index):
        if not index.isValid(): return
        s_data = self.model._data[index.row()]

        from PySide6.QtWidgets import QDialog, QFormLayout
        from utils.validator import Validator
        dialog = QDialog(self)
        dialog.setWindowTitle("تعديل بيانات مورد")
        d_layout = QFormLayout(dialog)

        name = QLineEdit(s_data['name'])
        Validator.setup_strict_validation(name, "name")
        phone = QLineEdit(s_data['phone'])
        Validator.setup_strict_validation(phone, "phone")
        email = QLineEdit(s_data['email'])
        address = QLineEdit(s_data['address'])

        d_layout.addRow("الاسم:", name)
        d_layout.addRow("الهاتف:", phone)
        d_layout.addRow("البريد:", email)
        d_layout.addRow("العنوان:", address)

        save = QPushButton("تحديث")
        save.clicked.connect(lambda: self.update_supplier(dialog, s_data['id'], {
            "name": name.text(), "phone": phone.text(), "email": email.text(),
            "address": address.text()
        }))
        d_layout.addRow(save)
        dialog.exec()

    def update_supplier(self, dialog, s_id, data):
        if not data['name']:
            QMessageBox.warning(self, "تنبيه", "الاسم مطلوب")
            return
        if self.service.update_supplier(s_id, data):
            dialog.accept()
            self.refresh()

    def handle_import(self):
        from views.import_wizard import EnterpriseImportWizard
        wizard = EnterpriseImportWizard(self.service, target="suppliers", parent=self)
        if wizard.exec():
            self.refresh()

    def handle_search(self):
        term = self.search_input.text()
        if term:
            results = self.service.search(term)
            self.refresh(results)
        else:
            self.refresh()

    def show_add_dialog(self):
        from PySide6.QtWidgets import QDialog, QFormLayout
        from utils.validator import Validator
        dialog = QDialog(self)
        dialog.setWindowTitle("إضافة مورد")
        d_layout = QFormLayout(dialog)

        name = QLineEdit()
        Validator.setup_strict_validation(name, "name")
        phone = QLineEdit()
        Validator.setup_strict_validation(phone, "phone")
        email = QLineEdit()
        address = QLineEdit()

        d_layout.addRow("الاسم:", name)
        d_layout.addRow("الهاتف:", phone)
        d_layout.addRow("البريد:", email)
        d_layout.addRow("العنوان:", address)

        save = QPushButton("حفظ")
        save.clicked.connect(lambda: self.save_supplier(dialog, {
            "name": name.text(), "phone": phone.text(), "email": email.text(),
            "address": address.text()
        }))
        d_layout.addRow(save)
        dialog.exec()

    def save_supplier(self, dialog, data):
        if not data['name']:
            QMessageBox.warning(self, "تنبيه", "الاسم مطلوب")
            return
        self.service.create_supplier(data)
        dialog.accept()
        self.refresh()

    def handle_delete(self, supplier_id):
        if QMessageBox.question(self, "تأكيد", "هل أنت متأكد من حذف هذا المورد؟") == QMessageBox.Yes:
            if self.service.delete_supplier(supplier_id):
                self.refresh()

    def closeEvent(self, event):
        Session.remove()
        event.accept()
