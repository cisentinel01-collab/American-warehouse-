from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QLabel, QGridLayout, QMessageBox, QProgressDialog)
from PySide6.QtCore import Qt, QThreadPool
import qtawesome as qta
from workers.worker import Worker
from utils.translation_manager import tr

class ReportsView(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.threadpool = QThreadPool.globalInstance()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Reports Grid
        grid = QGridLayout()

        self.create_report_item(grid, "تقرير المخزون الحالي", "fa5s.boxes", self.handle_inv_pdf, self.handle_inv_excel, 0, 0)
        self.create_report_item(grid, "تقرير الوارد", "fa5s.file-import", self.handle_in_pdf, self.handle_in_excel, 0, 1)
        self.create_report_item(grid, "تقرير الصادر", "fa5s.file-export", self.handle_out_pdf, self.handle_out_excel, 1, 0)
        self.create_report_item(grid, "تقرير النواقص", "fa5s.shopping-basket", self.handle_low_stock_pdf, self.handle_low_stock_excel, 1, 1)
        self.create_report_item(grid, "تقرير منتهى الصلاحية", "fa5s.calendar-times", self.handle_expired_pdf, None, 2, 0)
        self.create_report_item(grid, "سجل نشاط المستخدمين", "fa5s.user-shield", self.handle_audit_pdf, None, 2, 1)

        layout.addLayout(grid)
        layout.addStretch()

    def create_report_item(self, grid, title, icon, pdf_func, excel_func, r, c):
        group = QGroupBox(title)
        l = QVBoxLayout(group)

        pdf_btn = QPushButton(f"PDF {tr('reports')}")
        pdf_btn.setIcon(qta.icon("fa5s.file-pdf", color="#e74c3c"))
        pdf_btn.clicked.connect(pdf_func)
        l.addWidget(pdf_btn)

        if excel_func:
            excel_btn = QPushButton(f"Excel {tr('reports')}")
            excel_btn.setIcon(qta.icon("fa5s.file-excel", color="#27ae60"))
            excel_btn.clicked.connect(excel_func)
            l.addWidget(excel_btn)

        grid.addWidget(group, r, c)

    def _run_report_worker(self, func, *args, **kwargs):
        progress = QProgressDialog(tr("generating_report"), tr("cancel"), 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        def on_finished(path):
            progress.close()
            if path and path.endswith('.pdf'):
                from views.pdf_viewer import EmbeddedPDFViewer
                viewer = EmbeddedPDFViewer(path, self)
                viewer.exec()
            elif path:
                QMessageBox.information(self, tr("add_success"), f"{tr('report_saved')}: {path}")
            else:
                QMessageBox.warning(self, tr("error"), tr("report_failed"))

        worker = Worker(func, *args, **kwargs)
        worker.signals.result.connect(on_finished)
        self.threadpool.start(worker)

    def handle_inv_pdf(self):
        self._run_report_worker(self.controller.export_inventory_to_pdf, is_low_stock=False)

    def handle_inv_excel(self):
        self._run_report_worker(self.controller.export_inventory_to_excel, is_low_stock=False)

    def handle_low_stock_pdf(self):
        self._run_report_worker(self.controller.export_inventory_to_pdf, is_low_stock=True)

    def handle_low_stock_excel(self):
        self._run_report_worker(self.controller.export_inventory_to_excel, is_low_stock=True)

    def handle_in_pdf(self):
        self._run_report_worker(self.controller.export_movements_to_pdf, "IN")

    def handle_in_excel(self):
        self._run_report_worker(self.controller.export_movements_to_excel, "IN")

    def handle_out_pdf(self):
        self._run_report_worker(self.controller.export_movements_to_pdf, "OUT")

    def handle_out_excel(self):
        self._run_report_worker(self.controller.export_movements_to_excel, "OUT")

    def handle_audit_pdf(self):
        self._run_report_worker(self.controller.export_audit_to_pdf)

    def handle_expired_pdf(self):
        self._run_report_worker(self.controller.export_expiry_to_pdf, expired_only=True)
