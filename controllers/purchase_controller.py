from sqlalchemy.orm import Session
from models.inventory import Bin

class PurchaseController:
    def __init__(self, db: Session):
        self.db = db

    def get_pos(self):
        try:
            from models.inventory import Movement
            # Placeholder: fetch mock or draft purchase orders
            return []
        except:
            return []

    def generate_suggested_pos(self):
        return []

    def generate_po_pdf(self, po_id):
        return "reports/po_draft.pdf"
