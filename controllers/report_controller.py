from sqlalchemy.orm import Session
from services.report_service import ReportService
from datetime import datetime

class ReportController:
    def __init__(self, db: Session):
        self.db = db
        self.service = ReportService(db)

    def export_inventory_to_pdf(self, is_low_stock=False):
        return self.service.generate_inventory_report(is_low_stock=is_low_stock)

    def export_inventory_to_excel(self, is_low_stock=False):
        return self.service.generate_inventory_excel(is_low_stock=is_low_stock)

    def export_movements_to_pdf(self, m_type):
        return self.service.generate_movements_report(m_type, "pdf")

    def export_movements_to_excel(self, m_type):
        return self.service.generate_movements_report(m_type, "excel")

    def export_audit_to_pdf(self):
        return self.service.generate_audit_report()

    def export_expiry_to_pdf(self, expired_only=True):
        return self.service.generate_expiry_report()

    def get_stock_movements(self, start_date=None, end_date=None):
        return self.service.get_movements(start_date, end_date)
