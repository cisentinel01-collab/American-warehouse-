import sys
import os
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from views.login_view import LoginView
from database.migrate import migrate
from utils.device_manager import register_device, check_device_status
from app_logging.app_logger import app_logger
from database.session import Session
from utils.schema_validator import SchemaValidator


def main():
    # 1. Initialize Folders
    for d in ["reports", "backups", "images/barcodes", "logo"]:
        os.makedirs(d, exist_ok=True)

    # 2. Database Migration & Validation (Hardened)
    try:
        migrate()
        db = Session()
        valid, missing = SchemaValidator.validate_schema(db)
        if not valid:
            app_logger.warning(f"Schema inconsistent: {missing}. Attempting force migration.")
            migrate()
        db.close()
    except Exception as e:
        app_logger.critical(f"Critical Database Integrity Error: {e}\n{traceback.format_exc()}")

    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    # Vital: Don't quit when any window closes, let us manage the lifecycle
    app.setQuitOnLastWindowClosed(False)

    # 3. Global Exception Handling for PySide6
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        app_logger.error(f"Uncaught Exception: {err_msg}")

        QMessageBox.critical(
            None,
            "System Error",
            f"An unexpected error occurred:\n{str(exc_value)}\n\nPlease check the logs for details."
        )

    sys.excepthook = handle_exception

    # 4. Load Stylesheet
    try:
        style_path = os.path.join(os.path.dirname(__file__), "assets", "styles.qss")
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
    except Exception as e:
        app_logger.error(f"Style loading error: {e}")

    # 5. Device Security Check
    try:
        register_device()
        allowed, message = check_device_status()
        if not allowed:
            QMessageBox.critical(None, "Device Access Denied", message)
            sys.exit(1)
    except Exception as e:
        app_logger.error(f"Device Verification Error: {e}")
        QMessageBox.critical(None, "Security Error", f"Failed to verify device: {str(e)}")
        sys.exit(1)

    # 6. Initialize Main Window logic
    main_window = None

    def on_login_success(user_data):
        nonlocal main_window
        from views.main_window import MainWindow
        try:
            # Important: Switch to QuitOnLastWindowClosed=True once MainWindow is up
            app.setQuitOnLastWindowClosed(True)
            main_window = MainWindow()
            main_window.showMaximized()
        except Exception as e:
            app_logger.critical(f"MainWindow Initialization Failed: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(None, "Critical Error", f"Failed to initialize main interface: {str(e)}")
            sys.exit(1)

    # 7. Start with Login & Opening Balance Check
    from models.inventory import Settings, Item
    db = Session()
    sys_settings = db.query(Settings).first()
    if sys_settings and sys_settings.language:
        from utils.translation_manager import tr_manager
        tr_manager.set_language(sys_settings.language)
        app.setLayoutDirection(Qt.RightToLeft if tr_manager.is_rtl else Qt.LeftToRight)

    is_new_system = db.query(Item).count() == 0
    db.close()

    def on_opening_balance_needed():
        from views.import_wizard import EnterpriseImportWizard
        from services.item_service import ItemService
        wiz = EnterpriseImportWizard(ItemService(Session()), is_opening_balance=True)
        wiz.exec()

    # 7. Start Services
    from services.expiration_service import expiration_service
    expiration_service.start()

    login = LoginView()
    login.login_success.connect(on_login_success)
    login.show()

    # 8. Main Loop
    result = app.exec()

    # 9. Final Cleanup
    Session.remove()
    sys.exit(result)


if __name__ == "__main__":
    main()
