from sqlalchemy.orm import Session
from models.inventory import UnitOfMeasure, Item
from app_logging.app_logger import app_logger

class UOMService:
    def __init__(self, db: Session):
        self.db = db

    def convert_qty(self, item_id: int, qty: float, from_uom_id: int, to_uom_id: int) -> float:
        """
        Convert quantity between UOMs using reference ratios.
        """
        if from_uom_id == to_uom_id:
            return qty

        uom_from = self.db.query(UnitOfMeasure).filter(UnitOfMeasure.id == from_uom_id).first()
        uom_to = self.db.query(UnitOfMeasure).filter(UnitOfMeasure.id == to_uom_id).first()

        if not uom_from or not uom_to or uom_from.category != uom_to.category:
            app_logger.error(f"UOM Conversion failed: incompatible categories or UOM not found.")
            return qty

        # Logic: (Qty * From_Ratio) / To_Ratio
        return (qty * uom_from.ratio) / uom_to.ratio

    def get_uoms_by_category(self, category: str):
        return self.db.query(UnitOfMeasure).filter(UnitOfMeasure.category == category).all()
