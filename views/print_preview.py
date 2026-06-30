from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt
from PySide6.QtWebEngineWidgets import QWebEngineView
import qtawesome as qta
import os

class PrintPreviewDialog(QDialog):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        from utils.translation_manager import tr, tr_manager
        self.setWindowTitle(tr("document_preview"))
        self.resize(1000, 800)
        self.file_path = file_path
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)

        # Premium Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #2c3e50; border-bottom: 2px solid #d4af37;")
        toolbar_layout = QHBoxLayout(toolbar)

        from utils.translation_manager import tr
        title = QLabel(tr("document_preview").upper())
        title.setStyleSheet("color: #d4af37; font-weight: bold; margin-left: 20px;")
        toolbar_layout.addWidget(title)

        toolbar_layout.addStretch()

        external_btn = QPushButton(tr("open_externally"))
        external_btn.setIcon(qta.icon("fa5s.external-link-alt", color="white"))
        external_btn.setStyleSheet("color: white; border: 1px solid #7f8c8d; padding: 5px 15px; border-radius: 5px;")
        external_btn.clicked.connect(self.open_file)
        toolbar_layout.addWidget(external_btn)

        close_btn = QPushButton(qta.icon("fa5s.times", color="#e74c3c"), "")
        close_btn.setFixedSize(40, 40)
        close_btn.setStyleSheet("border: none;")
        close_btn.clicked.connect(self.accept)
        toolbar_layout.addWidget(close_btn)

        layout.addWidget(toolbar)

        # Internal PDF Viewer using WebEngine (Chromium-based)
        self.web_view = QWebEngineView()
        # Optimization: Clear cache on each load for freshness
        self.web_view.page().profile().clearHttpCache()
        # Set settings to allow local file access
        self.web_view.settings().setAttribute(self.web_view.settings().WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.web_view.settings().setAttribute(self.web_view.settings().WebAttribute.PluginsEnabled, True)

        # Convert path to URL
        from PySide6.QtCore import QUrl
        file_url = QUrl.fromLocalFile(os.path.abspath(self.file_path))
        self.web_view.load(file_url)

        layout.addWidget(self.web_view)

    def open_file(self):
        import subprocess, platform
        from PySide6.QtWidgets import QMessageBox
        try:
            path = os.path.abspath(self.file_path)
            if platform.system() == 'Darwin':       # macOS
                subprocess.call(('open', path))
            elif platform.system() == 'Windows':    # Windows
                os.startfile(path)
            else:                                   # linux variants
                subprocess.call(('xdg-open', path))
        except Exception as e:
            QMessageBox.critical(self, tr("error"), f"{tr('report_failed')}: {str(e)}")
