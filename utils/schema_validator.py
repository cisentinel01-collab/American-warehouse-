import os
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from app_logging.app_logger import app_logger

class SchemaValidator:
    @staticmethod
    def validate_schema(db: Session):
        """Validates that the database schema matches the expected enterprise structure."""
        inspector = inspect(db.get_bind())
        required_tables = ["users", "items", "movements", "batches", "suppliers", "locations", "settings"]

        existing_tables = inspector.get_table_names()
        missing_tables = [t for t in required_tables if t not in existing_tables]

        if missing_tables:
            app_logger.warning(f"Missing tables detected: {missing_tables}. Attempting auto-migration.")
            return False, missing_tables

        # Check critical columns (Example: barcode in items)
        item_cols = [c["name"] for c in inspector.get_columns("items")]
        if "barcode" not in item_cols:
            app_logger.warning("Critical column 'barcode' missing in 'items' table.")
            return False, ["items.barcode"]

        user_cols = [c["name"] for c in inspector.get_columns("users")]
        if "is_active" not in user_cols:
            app_logger.warning("Critical column 'is_active' missing in 'users' table.")
            return False, ["users.is_active"]

        return True, []
