from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QStackedWidget, QMessageBox, QFrame)
from PySide6.QtCore import Qt, QSize
import qtawesome as qta
import traceback

from views.dashboard_view import DashboardView
from views.items_view import ItemsView
from views.suppliers_view import SuppliersView
from views.stock_operations_view import StockOperationsView
from views.reports_view import ReportsView
from views.user_management_view import UserManagementView
from views.settings_view import SettingsView
from views.purchase_view import PurchaseView
from views.locations_view import LocationsView
from views.device_management_view import DeviceManagementView

from services.dashboard_service import DashboardService
from controllers.stock_controller import StockController
from controllers.report_controller import ReportController
from controllers.user_controller import UserController
from controllers.purchase_controller import PurchaseController
from controllers.device_controller import DeviceController
from services.report_service import ReportService
from services.item_service import ItemService
from services.supplier_service import SupplierService
from database.session import Session
from app_logging.app_logger import app_logger

from utils.auth import AuthManager
from models.inventory import Batch
from views.expiry_alarm_dialog import ExpiryAlarmDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        from utils.translation_manager import tr_manager
        self.setWindowTitle("American Marine Services - ERP")

        # 1. Immediate Direction Sync BEFORE layout construction
        is_rtl = tr_manager.is_rtl
        self.setLayoutDirection(Qt.RightToLeft if is_rtl else Qt.LeftToRight)
        from PySide6.QtWidgets import QApplication
        QApplication.instance().setLayoutDirection(Qt.RightToLeft if is_rtl else Qt.LeftToRight)

        try:
            self.db = Session()
            self.item_service = ItemService(self.db)
            self.supplier_service = SupplierService(self.db)

            self.setup_ui()
            self.init_views()

            from utils.translation_manager import lang_signal
            lang_signal.changed.connect(self.on_language_changed)

            self.load_dashboard()
            # Real-time expiration alarm connection
            from services.expiration_service import expiration_service
            expiration_service.expired_found.connect(self.on_expiration_detected)
            # self.check_expiry_alarm() # Initial check is handled by service.start()
        except Exception as e:
            app_logger.critical(f"MainWindow __init__ failure: {e}\n{traceback.format_exc()}")
            raise

    def init_views(self):
        # Lazy Loading Cache
        self.views_cache = {}

    def get_view(self, page_id):
        if page_id in self.views_cache:
            return self.views_cache[page_id]

        try:
            view = None
            if page_id == "dashboard":
                view = DashboardView(DashboardService(self.db))
            elif page_id == "items":
                view = ItemsView(self.item_service)
            elif page_id == "suppliers":
                view = SuppliersView(self.supplier_service)
            elif page_id == "stock_in":
                view = StockOperationsView(StockController(self.db), "IN")
            elif page_id == "stock_out":
                view = StockOperationsView(StockController(self.db), "OUT")
            elif page_id == "reports":
                view = ReportsView(ReportController(self.db))
            elif page_id == "users":
                view = UserManagementView(UserController(self.db))
            elif page_id == "devices":
                view = DeviceManagementView(DeviceController(self.db))
            elif page_id == "settings":
                view = SettingsView()
            elif page_id == "locations":
                view = LocationsView()
            elif page_id == "purchase":
                view = PurchaseView(PurchaseController(self.db))

            if view:
                self.views_cache[page_id] = view
                self.stack.addWidget(view)
            return view
        except Exception as e:
            app_logger.error(f"Error initializing view {page_id}: {e}")
            return None

    def on_expiration_detected(self, expired, soon):
        try:
            if expired or soon:
                dialog = ExpiryAlarmDialog(expired, soon, self)
                dialog.exec()
        except Exception as e:
            app_logger.error(f"Expiry alarm dialog failed: {e}")

    def setup_ui(self):
        from utils.translation_manager import tr_manager
        main_widget = self.centralWidget()
        if not main_widget:
            main_widget = QWidget()
            self.setCentralWidget(main_widget)

        # Clear existing layout if any (PySide6 compatible way)
        if main_widget.layout():
            # In PySide6, setting a new layout on a widget that already has one
            # will automatically delete the old one or we can explicitly orphan it.
            # The safest way is to delete the layout object itself.
            old_layout = main_widget.layout()
            # To truly clear it, we remove all items
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()
            import shiboken
            shiboken.delete(old_layout)

        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar Position Logic
        self.sidebar_pos = Qt.RightEdge if tr_manager.is_rtl else Qt.LeftEdge

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 20)
        sidebar_layout.setSpacing(5)

        # Logo/Brand (Sidebar)
        from utils.translation_manager import tr, tr_manager
        brand_container = QFrame()
        brand_vbox = QVBoxLayout(brand_container)

        sidebar_logo = QLabel()
        import os
        if os.path.exists("logo/logo.png"):
            from PySide6.QtGui import QPixmap
            sidebar_logo.setPixmap(QPixmap("logo/logo.png").scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            sidebar_logo.setPixmap(qta.icon("fa5s.shield-alt", color="#d4af37").pixmap(60, 60))
        sidebar_logo.setAlignment(Qt.AlignCenter)
        brand_vbox.addWidget(sidebar_logo)

        brand_label = QLabel("AMS FREEZONE")
        brand_label.setStyleSheet("color: #d4af37; font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        brand_label.setAlignment(Qt.AlignCenter)
        brand_vbox.addWidget(brand_label)

        sidebar_layout.addWidget(brand_container)
        self.nav_buttons = {}
        self.create_nav_button("dashboard", tr("dashboard"), "fa5s.chart-line")
        self.create_nav_button("items", tr("items"), "fa5s.boxes")
        self.create_nav_button("stock_in", tr("stock_in"), "fa5s.file-import")
        self.create_nav_button("stock_out", tr("stock_out"), "fa5s.file-export")
        self.create_nav_button("suppliers", tr("suppliers"), "fa5s.truck")
        self.create_nav_button("locations", tr("locations"), "fa5s.map-marker-alt")
        self.create_nav_button("purchase", tr("purchase"), "fa5s.shopping-cart")
        self.create_nav_button("reports", tr("reports"), "fa5s.file-alt")
        self.create_nav_button("users", tr("users"), "fa5s.users")
        self.create_nav_button("devices", tr("devices"), "fa5s.desktop")
        self.create_nav_button("settings", tr("settings"), "fa5s.cog")

        sidebar_layout.addStretch()

        logout_btn = QPushButton(tr("logout"))
        logout_btn.setIcon(qta.icon("fa5s.sign-out-alt", color="white"))
        logout_btn.clicked.connect(self.handle_logout)
        sidebar_layout.addWidget(logout_btn)

        # Content Area
        content_container = QWidget()
        self.content_layout = QVBoxLayout(content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        # Layout Ordering for Sidebar Flip
        if tr_manager.is_rtl:
            layout.addWidget(content_container, 1)
            layout.addWidget(self.sidebar)
        else:
            layout.addWidget(self.sidebar)
            layout.addWidget(content_container, 1)

        # Header
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(100)
        header_layout = QHBoxLayout(header)
        self.page_title = QLabel(tr("dashboard"))
        header_layout.addWidget(self.page_title)
        header_layout.addStretch()

        user = AuthManager.get_current_user()
        welcome_txt = "مرحباً" if tr_manager.current_language == 'ar' else "Welcome"
        user_info = QLabel(f"{welcome_txt}، {user['full_name'] if user else ''}")
        header_layout.addWidget(user_info)

        self.content_layout.addWidget(header)

        # Stacked Widget for pages
        self.stack = QStackedWidget()
        self.content_layout.addWidget(self.stack)

        layout.addWidget(content_container)

    def create_nav_button(self, id, text, icon_name):
        if not AuthManager.has_permission(id):
            return

        from utils.translation_manager import tr_manager
        btn = QPushButton(text)
        btn.setIcon(qta.icon(icon_name, color="white"))
        btn.setIconSize(QSize(22, 22))
        btn.setCheckable(True)
        btn.setAutoExclusive(True)

        # Premium Alignment: Icon on right for Arabic, left for English
        btn.setLayoutDirection(Qt.RightToLeft if tr_manager.is_rtl else Qt.LeftToRight)
        btn.setStyleSheet("text-align: left; padding: 12px 20px;" if not tr_manager.is_rtl else "text-align: right; padding: 12px 20px;")

        btn.clicked.connect(lambda: self.switch_page(id))
        self.sidebar.layout().addWidget(btn)
        self.nav_buttons[id] = btn

    def switch_page(self, page_id):
        if page_id not in self.nav_buttons: return
        try:
            self.nav_buttons[page_id].setChecked(True)
            self.page_title.setText(self.nav_buttons[page_id].text())

            view = self.get_view(page_id)
            if not view: return

            if hasattr(view, 'refresh'):
                view.refresh()
            elif hasattr(view, 'load_history'):
                view.load_history()
            elif hasattr(view, 'load_data'):
                view.load_data()

            if self.stack.currentWidget() != view:
                self.stack.setCurrentWidget(view)
        except Exception as e:
            app_logger.error(f"Navigation error to {page_id}: {e}")
            QMessageBox.critical(self, "خطأ في التنقل", f"فشل الانتقال إلى هذه الصفحة: {str(e)}")

    def on_language_changed(self, lang):
        # Apply Direction first
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        is_rtl = (lang == 'ar')
        app.setLayoutDirection(Qt.RightToLeft if is_rtl else Qt.LeftToRight)

        # Explicitly update MainWindow direction
        self.setLayoutDirection(Qt.RightToLeft if is_rtl else Qt.LeftToRight)

        # Vital: Clear the stack to prevent reference cycles and hanging
        while self.stack.count():
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.deleteLater()

        # Full UI Refresh by reconstructing central widget
        new_central = QWidget()
        self.setCentralWidget(new_central)

        self.init_views()
        self.setup_ui()

        # Reload current page text
        current_id = None
        for b_id, btn in self.nav_buttons.items():
            if btn.isChecked(): current_id = b_id; break

        if current_id:
            self.switch_page(current_id)

    def load_dashboard(self):
        if "dashboard" in self.nav_buttons:
            self.switch_page("dashboard")

    def handle_logout(self):
        AuthManager.logout()
        from views.login_view import LoginView
        from PySide6.QtWidgets import QApplication

        # Vital: Ensure app doesn't quit during window transition
        QApplication.instance().setQuitOnLastWindowClosed(False)

        self.login_window = LoginView()
        # Re-connect login success to a handler that re-opens MainWindow
        # In main.py we already have on_login_success which is nonlocal to main
        # But here we are in MainWindow. Let's restart the app logic or just show login.
        # Actually, the logic in main.py's on_login_success is what we want.
        # Since main.py's app.exec() is still running, showing LoginView is enough.

        # We need to reconnect the signal. We can't easily access the nonlocal in main.py.
        # Let's import the logic needed.
        def on_relogin(user_data):
            QApplication.instance().setQuitOnLastWindowClosed(True)
            self.new_main = MainWindow()
            self.new_main.showMaximized()

        self.login_window.login_success.connect(on_relogin)
        self.login_window.show()
        self.close()

    def closeEvent(self, event):
        # Cleanup session on close
        if hasattr(self, 'db'):
            Session.remove()
        event.accept()
