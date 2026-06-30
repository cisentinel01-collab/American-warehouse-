from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QLabel, QLineEdit, QFormLayout)
from PySide6.QtCore import Qt
import qtawesome as qta
from database.session import Session
from models.inventory import Settings

class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Session()
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        from PySide6.QtWidgets import QComboBox
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        group = QGroupBox("إعدادات الشركة")
        form = QFormLayout(group)
        form.setSpacing(15)

        self.name_input = QLineEdit()
        self.addr_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()

        form.addRow("اسم الشركة:", self.name_input)
        form.addRow("العنوان:", self.addr_input)
        form.addRow("الهاتف:", self.phone_input)
        form.addRow("البريد الإلكتروني:", self.email_input)

        self.lang_combo = QComboBox()
        self.lang_combo.addItem("العربية", "ar")
        self.lang_combo.addItem("English", "en")
        form.addRow("لغة النظام:", self.lang_combo)

        save_btn = QPushButton("حفظ التغييرات")
        save_btn.setObjectName("GoldButton")
        save_btn.setIcon(qta.icon("fa5s.save", color="black"))
        save_btn.clicked.connect(self.save_settings)
        form.addRow(save_btn)

        layout.addWidget(group)
        layout.addStretch()

    def load_settings(self):
        try:
            settings = self.db.query(Settings).first()
            if settings:
                self.name_input.setText(settings.company_name)
                self.addr_input.setText(settings.address or "")
                self.phone_input.setText(settings.phone or "")
                self.email_input.setText(settings.email or "")
                idx = self.lang_combo.findData(settings.language or "ar")
                self.lang_combo.setCurrentIndex(idx if idx != -1 else 0)
        except Exception as e:
            print(f"Load settings error: {e}")

    def save_settings(self):
        try:
            settings = self.db.query(Settings).first()
            if not settings:
                settings = Settings()
                self.db.add(settings)

            settings.company_name = self.name_input.text()
            settings.address = self.addr_input.text()
            settings.phone = self.phone_input.text()
            settings.email = self.email_input.text()

            new_lang = self.lang_combo.currentData()
            settings.language = new_lang

            self.db.commit()

            # Apply language change globally
            from utils.translation_manager import tr_manager, lang_signal
            tr_manager.set_language(new_lang)

            from PySide6.QtWidgets import QApplication, QMessageBox
            from PySide6.QtCore import Qt

            # Emit signal first to trigger layout flipping
            lang_signal.changed.emit(new_lang)

            QMessageBox.information(self, "نجاح / Success", "تم تغيير اللغة بنجاح وتطبيقها على كافة الواجهات.\nLanguage changed and applied to all views.")
        except Exception as e:
            self.db.rollback()
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "خطأ", f"فشل الحفظ: {str(e)}")

    def closeEvent(self, event):
        from database.session import Session
        Session.remove()
        event.accept()
