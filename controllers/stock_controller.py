from services.stock_service import StockService
from services.supplier_service import SupplierService
from services.item_service import ItemService
from sqlalchemy.orm import Session
import datetime

class StockController:
    def __init__(self, db: Session):
        self.db = db
        self.service = StockService(db)
        self.supplier_service = SupplierService(db)
        self.item_service = ItemService(db)

    def generate_invoice_no(self, type):
        return f"{type}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

    def receive_stock(self, data, items):
        # Adapt UI items format to service format
        adapted_items = []
        for it in items:
            batch = it.get('batch_info', {})
            adapted_items.append({
                'item_id': it['item_id'],
                'qty': it['quantity'],
                'price': it['price'],
                'bin_id': 1,
                'lot_number': batch.get('batch_number', 'DEFAULT'),
                'expiry': batch.get('expiry_date')
            })
        movement_data = data.copy()
        movement_data['type'] = 'IN'
        movement_data['ref'] = data['reference_no']

        success = self.service.record_movement(movement_data, adapted_items)
        return success, []

    def issue_stock(self, data, items):
        adapted_items = []
        for it in items:
            adapted_items.append({
                'item_id': it['item_id'],
                'qty': it['quantity'],
                'price': it['price'],
                'bin_id': 1
            })
        movement_data = data.copy()
        movement_data['type'] = 'OUT'
        movement_data['ref'] = data['reference_no']

        success = self.service.record_movement(movement_data, adapted_items)
        return success, []

    def get_movement_history(self, **kwargs):
        return self.service.get_history(**kwargs)

    def get_suppliers(self):
        return self.supplier_service.get_all()

    def get_items(self, limit=100):
        return self.item_service.get_items(limit=limit)

    def search_items(self, query):
        return self.item_service.search_items(query)

    def get_item_by_code(self, code):
        return self.item_service.get_item_by_code(code)

    def generate_movement_pdf(self, m_id):
        # In a real ERP, this would use a movement-specific report generator
        return self.service.generate_invoice_pdf(m_id)
