from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFrame)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
import os

class EmbeddedPDFViewer(QDialog):
    def __init__(self, pdf_path, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.setWindowTitle("AMS ERP - Report Viewer")
        self.resize(1000, 800)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Custom Toolbar
        toolbar = QFrame()
        toolbar.setFixedHeight(50)
        toolbar.setStyleSheet("background-color: #2c3e50; color: white;")
        t_layout = QHBoxLayout(toolbar)

        self.title_lbl = QLabel(os.path.basename(self.pdf_path))
        self.title_lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
        t_layout.addWidget(self.title_lbl)
        t_layout.addStretch()

        zoom_in = QPushButton("+")
        zoom_in.clicked.connect(lambda: self.browser.setZoomFactor(self.browser.zoomFactor() + 0.1))
        t_layout.addWidget(zoom_in)

        zoom_out = QPushButton("-")
        zoom_out.clicked.connect(lambda: self.browser.setZoomFactor(self.browser.zoomFactor() - 0.1))
        t_layout.addWidget(zoom_out)

        rotate_btn = QPushButton("Rotate")
        rotate_btn.clicked.connect(self.handle_rotate)
        t_layout.addWidget(rotate_btn)

        print_btn = QPushButton("Print")
        print_btn.clicked.connect(self.handle_print)
        t_layout.addWidget(print_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        t_layout.addWidget(close_btn)

        layout.addWidget(toolbar)

        # WebEngine Viewer (using PDF.js or native browser support)
        self.browser = QWebEngineView()
        # QWebEngineView can load PDF directly in most modern builds
        # We use file:// URL
        abs_path = os.path.abspath(self.pdf_path)
        self.browser.setUrl(QUrl.fromLocalFile(abs_path))
        layout.addWidget(self.browser)

    def handle_print(self):
        self.browser.page().printToPdf(self.pdf_path.replace(".pdf", "_print.pdf"))
        # In a real environment, we'd trigger system print dialog
        pass

    def handle_rotate(self):
        # Inject JS to rotate the PDF (simplified)
        self.browser.page().runJavaScript("document.body.style.transform += 'rotate(90deg)';")
