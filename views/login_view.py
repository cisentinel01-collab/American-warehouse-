from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QLabel, QMessageBox, QFrame)
from PySide6.QtCore import Qt, Signal
import qtawesome as qta
import traceback
from utils.auth import AuthManager
from app_logging.app_logger import app_logger

class LoginView(QWidget):
    login_success = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("تسجيل الدخول - نظام إدارة المخازن")
        self.setMinimumSize(450, 550)
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Background/Container
        self.container = QFrame()
        self.container.setObjectName("LoginContainer")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(40, 40, 40, 40)
        container_layout.setSpacing(20)

        from utils.translation_manager import tr
        # Logo
        logo_label = QLabel()
        logo_label.setPixmap(qta.icon("fa5s.warehouse", color="#d4af37").pixmap(80, 80))
        logo_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(logo_label)

        title = QLabel("AMS FREEZONE")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #d4af37;")
        title.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title)

        subtitle = QLabel(tr("system_subtitle"))
        subtitle.setStyleSheet("font-size: 14px; color: #ecf0f1;")
        subtitle.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(subtitle)

        # Inputs
        self.username = QLineEdit()
        self.username.setPlaceholderText(tr("username"))
        self.username.setMinimumHeight(50)
        container_layout.addWidget(self.username)

        self.password = QLineEdit()
        self.password.setPlaceholderText(tr("password"))
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setMinimumHeight(50)
        self.password.returnPressed.connect(self.handle_login)
        container_layout.addWidget(self.password)

        # Login Button
        self.login_btn = QPushButton(tr("login"))
        self.login_btn.setObjectName("GoldButton")
        self.login_btn.setMinimumHeight(55)
        self.login_btn.clicked.connect(self.handle_login)
        container_layout.addWidget(self.login_btn)

        container_layout.addStretch()
        self.main_layout.addWidget(self.container)

    def handle_login(self):
        user = self.username.text()
        pw = self.password.text()

        if not user or not pw:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال اسم المستخدم وكلمة المرور")
            return

        try:
            from database.session import Session
            from services.auth_service import AuthService

            # Using scoped session for auth
            db = Session()
            auth_service = AuthService(db)
            authenticated_user = auth_service.authenticate(user, pw)

            if authenticated_user:
                user_data = {
                    "id": authenticated_user.id,
                    "username": authenticated_user.username,
                    "full_name": authenticated_user.full_name,
                    "role": authenticated_user.role
                }
                AuthManager._current_user = user_data
                self.login_success.emit(user_data)
                self.close()
            else:
                QMessageBox.critical(self, "خطأ", "اسم المستخدم أو كلمة المرور غير صحيحة، أو الحساب غير نشط")
        except Exception as e:
            app_logger.error(f"Login logic failure: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "خطأ في النظام", f"فشل تسجيل الدخول بسبب خطأ داخلي: {str(e)}")
        finally:
            # scoped_session.remove() is vital
            from database.session import Session
            Session.remove()
