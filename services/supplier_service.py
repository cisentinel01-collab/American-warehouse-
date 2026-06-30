from sqlalchemy.orm import Session
from repositories.supplier_repo import SupplierRepository
from models.inventory import Supplier
from app_logging.app_logger import app_logger
from utils.signals import signal_manager

class SupplierService:
    def __init__(self, db: Session):
        self._repo = SupplierRepository(db)
        self.db = db

    def get_all(self):
        try:
            return self._repo.get_all()
        except Exception as e:
            app_logger.error(f"SupplierService.get_all error: {e}")
            raise

    def create_supplier(self, data: dict):
        try:
            new_s = Supplier(**data)
            res = self._repo.create(new_s)
            signal_manager.supplier_changed.emit()
            return res
        except Exception as e:
            app_logger.error(f"SupplierService.create_supplier error: {e}")
            raise

    def update_supplier(self, s_id: int, data: dict):
        try:
            supplier = self._repo.get_by_id(s_id)
            if supplier:
                return self._repo.update(supplier, data)
            return None
        except Exception as e:
            app_logger.error(f"SupplierService.update_supplier error: {e}")
            raise

    def delete_supplier(self, s_id: int):
        try:
            return self._repo.delete(s_id)
        except Exception as e:
            app_logger.error(f"SupplierService.delete_supplier error: {e}")
            raise

    def get_supplier_by_id(self, s_id: int):
        return self._repo.get_by_id(s_id)

    def search(self, term: str):
        return self._repo.search(term)
