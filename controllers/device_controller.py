from sqlalchemy.orm import Session
from sqlalchemy import text
from app_logging.app_logger import app_logger

class DeviceController:
    def __init__(self, db: Session):
        self.db = db

    def get_all_devices(self):
        try:
            # Simple check if devices table exists via raw query
            res = self.db.execute(text("SELECT * FROM devices")).mappings().all()
            return [dict(r) for r in res]
        except:
            return []

    def activate_device(self, d_id, expiry_date):
        try:
            self.db.execute(
                text("UPDATE devices SET status = 'active', expiry_date = :expiry WHERE id = :id"),
                {"expiry": expiry_date, "id": d_id}
            )
            self.db.commit()
            return True
        except:
            self.db.rollback()
            return False

    def block_device(self, d_id):
        try:
            self.db.execute(
                text("UPDATE devices SET status = 'blocked' WHERE id = :id"),
                {"id": d_id}
            )
            self.db.commit()
            return True
        except:
            self.db.rollback()
            return False

    def delete_device(self, d_id):
        try:
            self.db.execute(
                text("DELETE FROM devices WHERE id = :id"),
                {"id": d_id}
            )
            self.db.commit()
            return True
        except:
            self.db.rollback()
            return False
