from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableView,
                             QPushButton, QLineEdit, QLabel,
                             QHeaderView, QDialog, QFormLayout, QComboBox,
                             QSpinBox, QMessageBox, QFileDialog, QInputDialog)
from PySide6.QtCore import Qt, Signal, QTimer, QThreadPool
import qtawesome as qta
import os
from utils.auth import AuthManager
from utils.translation_manager import tr, tr_manager
from views_components.enterprise_table_model import EnterpriseTableModel
from workers.worker import Worker
from utils.signals import signal_manager

class ItemsView(QWidget):
    data_changed = Signal()

    def __init__(self, item_service):
        super().__init__()
        self.service = item_service
        self.threadpool = QThreadPool()
        self.current_page = 0
        self.page_size = 50

        # Search debounce timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

        self.setup_ui()

    def setup_ui(self):
        from utils.translation_manager import tr
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Toolbar
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("search_items_placeholder"))
        self.search_input.textChanged.connect(self.handle_search)
        toolbar.addWidget(self.search_input)

        # Pagination Controls
        pagination_layout = QHBoxLayout()
        self.prev_btn = QPushButton()
        self.prev_btn.setIcon(qta.icon("fa5s.chevron-right" if tr_manager.is_rtl else "fa5s.chevron-left", color="#1a2a6c"))
        self.prev_btn.setFixedSize(35, 35)
        self.prev_btn.clicked.connect(self.prev_page)

        self.next_btn = QPushButton()
        self.next_btn.setIcon(qta.icon("fa5s.chevron-left" if tr_manager.is_rtl else "fa5s.chevron-right", color="#1a2a6c"))
        self.next_btn.setFixedSize(35, 35)
        self.next_btn.clicked.connect(self.next_page)

        self.page_label = QLabel(f"{tr('page')} {self.current_page + 1}")
        self.page_label.setStyleSheet("font-weight: bold; margin: 0 10px;")

        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.prev_btn)
        toolbar.addLayout(pagination_layout)

        add_btn = QPushButton(tr("add_item"))
        add_btn.setObjectName("PrimaryButton")
        add_btn.setIcon(qta.icon("fa5s.plus", color="white"))
        add_btn.setEnabled(AuthManager.has_permission('items', 'add'))
        add_btn.clicked.connect(self.show_add_dialog)
        toolbar.addWidget(add_btn)

        import_btn = QPushButton(tr("import_excel"))
        import_btn.setObjectName("SecondaryButton")
        import_btn.setEnabled(AuthManager.has_permission('items', 'add'))
        import_btn.clicked.connect(self.handle_import)
        toolbar.addWidget(import_btn)

        layout.addLayout(toolbar)

        # Table
        self.view = QTableView()
        self.view.setEditTriggers(QTableView.NoEditTriggers)
        self.view.setSelectionBehavior(QTableView.SelectRows)
        self.view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.view)

        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.show_context_menu)
        self.view.doubleClicked.connect(self.handle_analysis)

        self.headers = ["code", "name", "category", "unit", "current_stock", "min_stock", "actions"]
        self.translated_headers = [tr("item_code"), tr("item_name"), tr("category"), tr("unit"), tr("current_stock"), tr("min_stock"), tr("actions")]
        self.model = EnterpriseTableModel([], self.headers, self.translated_headers)
        self.view.setModel(self.model)

        self.refresh()
        signal_manager.item_changed.connect(self.refresh)

    def refresh(self, items=None):
        if items is not None:
            self.on_data_loaded(items)
            return

        worker = Worker(self.service.get_items, skip=self.current_page * self.page_size, limit=self.page_size)
        worker.signals.result.connect(self.on_data_loaded)
        self.threadpool.start(worker)

    def on_data_loaded(self, items):
        from utils.translation_manager import tr
        data = []
        for i in items:
            # Prefer 'unit' text column, fallback to uom.name
            u_text = i.unit if hasattr(i, 'unit') and i.unit else (i.uom.name if i.uom else "")
            data.append({
                "id": i.id,
                "code": i.code,
                "name": i.name,
                "category": i.category,
                "unit": u_text,
                "current_stock": i.current_stock,
                "min_stock": i.min_stock,
                "actions": tr("view_analysis")
            })
        self.model.update_data(data)
        self.page_label.setText(f"صفحة {self.current_page + 1}")
        self.next_btn.setEnabled(len(items) == self.page_size)
        self.prev_btn.setEnabled(self.current_page > 0)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh()

    def next_page(self):
        self.current_page += 1
        self.refresh()

    def handle_search(self):
        self.search_timer.start(300)

    def perform_search(self):
        term = self.search_input.text()
        if term:
            self.current_page = 0
            items = self.service.search_items(term)
            self.refresh(items)
        else:
            self.current_page = 0
            self.refresh()

    def show_add_dialog(self):
        dialog = ItemDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            self.service.create_item(data)
            self.refresh()
            self.data_changed.emit()

    def handle_import(self):
        from views.import_wizard import EnterpriseImportWizard
        wizard = EnterpriseImportWizard(self.service, self)
        if wizard.exec():
            self.refresh()
            self.data_changed.emit()

    def show_context_menu(self, pos):
        from PySide6.QtWidgets import QMenu
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
            self.handle_delete(index)

    def handle_analysis(self, index):
        if not index.isValid(): return
        item_id = self.model._data[index.row()].get("id")
        if item_id:
            # For now re-use the item details or create analysis
            QMessageBox.information(self, tr("view_analysis"), f"Analysis for Item ID: {item_id}")

    def handle_edit(self, index):
        if not index.isValid(): return
        item_data = self.model._data[index.row()]
        item_id = item_data.get("id")

        dialog = ItemDialog(self, item_data=item_data)
        if dialog.exec():
            data = dialog.get_data()
            # Ensure price/quantity etc are handled as floats in the service
            self.service.update_item(item_id, data)
            self.refresh()
            self.data_changed.emit()

    def handle_delete(self, index):
        if not index.isValid(): return
        item_id = self.model._data[index.row()].get("id")
        if QMessageBox.question(self, tr("confirm"), tr("delete_confirm")) == QMessageBox.Yes:
            self.service.delete_item(item_id)
            self.refresh()
            self.data_changed.emit()

class ItemDialog(QDialog):
    def __init__(self, parent=None, item_data=None):
        super().__init__(parent)
        self.item_data = item_data
        from utils.translation_manager import tr, tr_manager
        self.setWindowTitle(tr("edit") if item_data else tr("add_item"))
        self.resize(500, 500)
        self.setLayoutDirection(Qt.RightToLeft if tr_manager.is_rtl else Qt.LeftToRight)
        self.setup_ui()

    def setup_ui(self):
        from utils.translation_manager import tr, tr_manager
        layout = QFormLayout(self)
        layout.setLabelAlignment(Qt.AlignRight if tr_manager.is_rtl else Qt.AlignLeft)
        from utils.validator import Validator

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("مثال: ITEM-101")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("أدخل اسم الصنف")
        Validator.setup_strict_validation(self.name_input, "name")

        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("مثال: قطع غيار")

        self.uom_input = QLineEdit()

        if self.item_data:
            self.code_input.setText(str(self.item_data.get('code', '')))
            self.name_input.setText(str(self.item_data.get('name', '')))
            self.category_input.setText(str(self.item_data.get('category', '')))
            self.uom_input.setText(str(self.item_data.get('unit', '')))

        self.min_stock_input = QSpinBox()
        self.min_stock_input.setMaximum(1000000)

        self.location_combo = QComboBox()
        from models.inventory import Location
        from database.session import Session
        db = Session()
        locations = db.query(Location).filter(Location.active == True).all()
        for loc in locations:
            self.location_combo.addItem(loc.name, loc.id)
        db.close()

        self.supplier_combo = QComboBox()
        from models.inventory import Supplier
        db = Session()
        suppliers = db.query(Supplier).filter(Supplier.is_deleted == False).all()
        for s in suppliers:
            self.supplier_combo.addItem(s.name, s.id)
        db.close()

        layout.addRow(tr("item_code") + ":", self.code_input)
        layout.addRow(tr("item_name") + ":", self.name_input)
        layout.addRow(tr("category") + ":", self.category_input)
        layout.addRow(tr("unit") + ":", self.uom_input)
        layout.addRow(tr("locations") + ":", self.location_combo)
        layout.addRow(tr("suppliers") + ":", self.supplier_combo)
        layout.addRow(tr("min_stock") + ":", self.min_stock_input)

        btns = QHBoxLayout()
        save_btn = QPushButton(tr("save"))
        save_btn.setObjectName("PrimaryButton")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton(tr("cancel"))
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addRow(btns)

    def accept(self):
        from utils.validator import Validator
        if not Validator.is_not_empty(self.code_input.text()) or \
           not Validator.is_not_empty(self.name_input.text()):
            QMessageBox.warning(self, "تنبيه", "يرجى ملأ الخانات الأساسية (الكود والاسم)")
            return
        super().accept()

    def get_data(self):
        return {
            "code": self.code_input.text(),
            "name": self.name_input.text(),
            "category": self.category_input.text(),
            "unit": self.uom_input.text(),
            "location_id": self.location_combo.currentData(),
            "supplier_id": self.supplier_combo.currentData(),
            "min_stock": self.min_stock_input.value()
        }
