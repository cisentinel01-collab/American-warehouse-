from PySide6.QtCore import QObject, QTimer, Signal
from models.inventory import Batch
from database.session import Session
from utils.signals import signal_manager
from app_logging.app_logger import app_logger
from datetime import datetime

class ExpirationService(QObject):
    expired_found = Signal(list, list) # expired, soon

    def __init__(self, check_interval_ms=3600000): # Default 1 hour
        super().__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_expirations)
        self.check_interval = check_interval_ms

    def start(self):
        self.timer.start(self.check_interval)
        # Immediate check on start
        self.check_expirations()

    def check_expirations(self):
        try:
            from sqlalchemy.orm import joinedload
            db = Session()
            # Eager load 'item' to avoid DetachedInstanceError in background thread
            expired = db.query(Batch).options(joinedload(Batch.item)).filter(
                Batch.expiry_date < datetime.utcnow().date(),
                Batch.quantity > 0
            ).all()

            from datetime import timedelta
            future_date = datetime.utcnow().date() + timedelta(days=6*30)
            soon = db.query(Batch).options(joinedload(Batch.item)).filter(
                Batch.expiry_date >= datetime.utcnow().date(),
                Batch.expiry_date <= future_date,
                Batch.quantity > 0
            ).all()

            if expired or soon:
                self.expired_found.emit(expired, soon)
                # Also notify via global signals to update dashboard
                signal_manager.item_changed.emit()
        except Exception as e:
            app_logger.error(f"Expiration check failed: {e}")
        finally:
            Session.remove()

expiration_service = ExpirationService()
