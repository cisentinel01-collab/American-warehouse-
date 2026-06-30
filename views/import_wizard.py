from PySide6.QtWidgets import (QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFileDialog, QTableWidget,
                             QTableWidgetItem, QComboBox, QMessageBox, QFrame,
                             QProgressBar, QScrollArea, QWidget, QDateEdit, QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt, Signal, QThreadPool
import pandas as pd
from utils.translation_manager import tr, tr_manager
from workers.worker import Worker

class EnterpriseImportWizard(QWizard):
    def __init__(self, service, target="items", parent=None, is_opening_balance=False, prefilled_data=None):
        super().__init__(parent)
        self.service = service
        self.target = target # "items", "suppliers", "movements"
        self.is_opening_balance = is_opening_balance
        self.import_data = prefilled_data
        self.setWindowTitle(tr("import_wizard") + (" - " + tr("opening_balance") if is_opening_balance else ""))
        self.resize(1100, 800)
        self.setStyleSheet("""
            QWizard { background-color: #1a1c23; color: #ecf0f1; }
            QWizardPage { background-color: #1a1c23; }
            QLabel { color: #ecf0f1; font-size: 13px; }
            QPushButton { border-radius: 5px; padding: 8px 15px; }
            QTableWidget { background-color: #242730; color: #ecf0f1; border: 1px solid #333; gridline-color: #444; }
            QTableWidget::item { color: #ecf0f1; }
            QHeaderView::section { background-color: #2c3e50; color: #d4af37; font-weight: bold; border: 1px solid #333; }
            QComboBox { background-color: #2c3e50; color: white; border: 1px solid #444; padding: 5px; }
            QDateEdit { background-color: #2c3e50; color: white; border: 1px solid #444; }
        """)
        # Center the wizard on screen
        if parent:
            self.move(parent.window().frameGeometry().center() - self.frameGeometry().center())
        self.setWizardStyle(QWizard.ModernStyle)
        self.setLayoutDirection(Qt.RightToLeft if tr_manager.is_rtl else Qt.LeftToRight)

        self.import_data = None
        self.mapping = {}
        self.undo_stack = []
        self.templates = {} # Key: template_name, Value: mapping_dict

        # 1. Type Selection (Global)
        self.invoice_type = "IN" # Default

        # Steps
        self.addPage(TypeSelectionPage(self))
        self.addPage(UploadPage(self))
        self.addPage(MappingPage(self))
        self.addPage(ValidationPage(self))
        self.addPage(SuccessPage(self))

    def cleanup(self):
        # Prevent memory leaks
        self.import_data = None
        self.mapping = {}

class TypeSelectionPage(QWizardPage):
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.setTitle(tr("select_invoice_type"))
        layout = QVBoxLayout(self)

        self.group = QButtonGroup(self)
        self.in_radio = QRadioButton(tr("incoming"))
        self.in_radio.setChecked(True)
        self.out_radio = QRadioButton(tr("outgoing"))

        self.group.addButton(self.in_radio)
        self.group.addButton(self.out_radio)

        layout.addWidget(self.in_radio)
        layout.addWidget(self.out_radio)
        layout.addStretch()

    def validatePage(self):
        self.wizard.invoice_type = "IN" if self.in_radio.isChecked() else "OUT"
        return True

class UploadPage(QWizardPage):
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.setTitle(tr("step_upload"))
        layout = QVBoxLayout(self)

        self.btn = QPushButton(tr("select_file"))
        self.btn.setObjectName("PrimaryButton")
        self.btn.clicked.connect(self.load_file)
        layout.addWidget(self.btn)

        self.file_label = QLabel(tr("no_file_selected"))
        self.file_label.setStyleSheet("color: #d4af37; font-weight: bold;")
        layout.addWidget(self.file_label)

        self.pbar = QProgressBar()
        self.pbar.setVisible(False)
        layout.addWidget(self.pbar)

        self.preview = QTableWidget()
        layout.addWidget(self.preview)

    def initializePage(self):
        if self.wizard.import_data is not None:
            self.file_label.setText(tr("prefilled_data"))
            self.show_preview()

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("select_file"), "", "All Supported (*.xlsx *.xls *.csv *.pdf *.jpg *.png);;Excel (*.xlsx *.xls);;CSV (*.csv);;PDF (*.pdf);;Images (*.jpg *.png)")
        if path:
            self.btn.setEnabled(False)
            self.pbar.setVisible(True)
            self.pbar.setRange(0, 0)
            self.file_label.setText(tr("loading_data_wait"))

            from services.import_service import ImportService
            svc = ImportService()

            def extraction_task():
                if path.lower().endswith(('.xlsx', '.xls', '.csv')):
                    return pd.DataFrame(svc.extract_from_excel(path))
                elif path.lower().endswith('.pdf'):
                    return pd.DataFrame(svc.extract_from_pdf(path))
                else:
                    return pd.DataFrame(svc.extract_from_image(path))

            def on_finished(df):
                self.wizard.import_data = df
                self.file_label.setText(path)
                self.show_preview()
                self.btn.setEnabled(True)
                self.pbar.setVisible(False)
                self.completeChanged.emit()

            def on_error(err):
                QMessageBox.critical(self, tr("error"), f"Extraction failed: {err}")
                self.btn.setEnabled(True)
                self.pbar.setVisible(False)

            worker = Worker(extraction_task)
            worker.signals.result.connect(on_finished)
            worker.signals.error.connect(on_error)
            QThreadPool.globalInstance().start(worker)

    def show_preview(self):
        df = self.wizard.import_data.head(10)
        self.preview.setRowCount(df.shape[0])
        self.preview.setColumnCount(df.shape[1])
        self.preview.setHorizontalHeaderLabels(df.columns)
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                self.preview.setItem(i, j, QTableWidgetItem(str(df.iloc[i, j])))

    def isComplete(self):
        return self.wizard.import_data is not None

class MappingPage(QWizardPage):
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.setTitle(tr("step_mapping"))
        self.layout = QVBoxLayout(self)

    def initializePage(self):
        # Clear layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        self.layout.addWidget(QLabel(tr("map_columns_info")))

        # Stock Operation Global Dates (Intelligent Batch Management)
        from PySide6.QtWidgets import QGridLayout
        if self.wizard.target == "movements":
            self.date_group = QFrame()
            self.date_group.setStyleSheet("background: #242730; border: 1px solid #d4af37; border-radius: 10px; margin-bottom: 10px;")
            dv = QVBoxLayout(self.date_group)
            header_lbl = QLabel(tr("global_batch_dates").upper())
            header_lbl.setStyleSheet("color: #d4af37; font-weight: bold;")
            dv.addWidget(header_lbl)

            dh = QHBoxLayout()
            self.global_prod = QDateEdit()
            self.global_prod.setCalendarPopup(True)
            self.global_exp = QDateEdit()
            self.global_exp.setCalendarPopup(True)
            from PySide6.QtCore import QDate
            self.global_prod.setDate(QDate.currentDate())
            self.global_exp.setDate(QDate.currentDate().addYears(1))

            dh.addWidget(QLabel(tr("production_date") + ":"))
            dh.addWidget(self.global_prod)
            dh.addWidget(QLabel(tr("expiry_date") + ":"))
            dh.addWidget(self.global_exp)
            dv.addLayout(dh)
            self.layout.addWidget(self.date_group)

        # Enterprise Mapping Grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        container = QWidget()
        mapping_grid = QGridLayout(container)
        mapping_grid.setSpacing(20)

        if self.wizard.target == "suppliers":
            target_fields = ['name', 'phone', 'email', 'address']
        elif self.wizard.target == "movements":
            target_fields = ['code', 'name', 'quantity', 'price', 'production_date', 'expiry_date', 'supplier', 'invoice_no', 'invoice_date', 'taxes', 'notes']
        else:
            target_fields = ['code', 'name', 'category', 'unit', 'min_stock', 'current_stock']

        self.combos = {}

        for idx, field in enumerate(target_fields):
            lbl = QLabel(tr(f"field_{field}") + ":")
            lbl.setStyleSheet("font-weight: bold; color: #d4af37;")
            mapping_grid.addWidget(lbl, idx, 0)

            combo = QComboBox()
            combo.addItem("-- Select --", None)
            cols = self.wizard.import_data.columns.tolist()
            combo.addItems(cols)

            # Smart Auto-Detection
            from thefuzz import process
            match, score = process.extractOne(field, cols)
            if score > 70:
                combo.setCurrentText(match)

            self.combos[field] = combo
            mapping_grid.addWidget(combo, idx, 1)

        scroll.setWidget(container)
        self.layout.addWidget(scroll)

    def validatePage(self):
        self.wizard.mapping = {f: c.currentText() for f, c in self.combos.items() if c.currentIndex() > 0}

        # Validation Logic
        if self.wizard.target == "suppliers":
            if 'name' not in self.wizard.mapping:
                QMessageBox.warning(self, tr("warning"), tr("mapping_required_fields_suppliers"))
                return False
        else:
            if 'code' not in self.wizard.mapping or 'name' not in self.wizard.mapping:
                QMessageBox.warning(self, tr("warning"), tr("mapping_required_fields"))
                return False
        return True

class ValidationPage(QWizardPage):
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.setTitle(tr("step_validation"))
        self.layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.layout.addWidget(self.table)
        self.errors = []

    def initializePage(self):
        df = self.wizard.import_data
        mapping = self.wizard.mapping
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(mapping) + 1)
        self.table.setHorizontalHeaderLabels(list(mapping.keys()) + ["Status"])

        self.errors = []
        # Optimization: Fetch existing codes to check duplicates
        existing_codes = []
        if self.wizard.target == "items":
            from database.session import Session
            from models.inventory import Item
            db = Session()
            existing_codes = [c[0] for c in db.query(Item.code).all()]
            db.close()

        for idx, row in df.iterrows():
            status = "✅ OK"
            row_err = False
            for col_idx, (field, excel_col) in enumerate(mapping.items()):
                val = row[excel_col]
                item = QTableWidgetItem(str(val))

                # Validation Logic
                if field == 'code':
                    if pd.isna(val):
                        status = "❌ Missing Code"; row_err = True
                        item.setBackground(Qt.red)
                    elif str(val) in existing_codes:
                        status = "⚠️ Duplicate (Will Update)";
                        item.setBackground(Qt.yellow)

                if field == 'current_stock' and pd.isna(val):
                    val = 0.0

                self.table.setItem(idx, col_idx, item)

            if row_err: self.errors.append(idx)
            self.table.setItem(idx, len(mapping), QTableWidgetItem(status))

    def validatePage(self):
        if self.errors:
            return QMessageBox.question(self, tr("confirm"), tr("proceed_with_errors")) == QMessageBox.Yes
        return True

class SuccessPage(QWizardPage):
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.setTitle(tr("step_import"))
        layout = QVBoxLayout(self)
        self.lbl = QLabel(tr("ready_to_import"))
        layout.addWidget(self.lbl)
        self.pbar = QProgressBar()
        layout.addWidget(self.pbar)
        self.final_data = []

    def initializePage(self):
        # Final Execution
        df = self.wizard.import_data
        mapping = self.wizard.mapping
        total = len(df)
        self.pbar.setMaximum(total)

        count = 0
        self.final_data = []
        for _, row in df.iterrows():
            data = {}
            for field, excel_col in mapping.items():
                data[field] = row[excel_col]

            try:
                if self.wizard.target == "suppliers":
                    self.wizard.service.create_supplier(data)
                    count += 1
                elif self.wizard.target == "movements":
                    # Smart Date Overrides
                    if hasattr(self.wizard, 'global_prod'):
                        data['production_date'] = data.get('production_date') or self.wizard.global_prod.date().toString("yyyy-MM-dd")
                        data['expiry_date'] = data.get('expiry_date') or self.wizard.global_exp.date().toString("yyyy-MM-dd")
                    self.final_data.append(data)
                    count += 1
                else:
                    self.wizard.service.create_item(data)
                    count += 1

                self.pbar.setValue(count)
            except:
                pass

        self.lbl.setText(f"Successfully Processed {count} records!")
