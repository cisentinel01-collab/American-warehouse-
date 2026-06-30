from database.session import engine, Base
import os
from sqlalchemy import text
from app_logging.app_logger import app_logger

# Ensure all models are imported for metadata
from models.user import User
from models.inventory import Warehouse, Zone, Bin, Item, StockLot, StockQuant, UnitOfMeasure, Supplier, Location, Movement, Settings
from models.audit import AuditLog

def migrate():
    app_logger.info("Initializing Enterprise Database schema...")

    # 1. Create tables from models
    Base.metadata.create_all(bind=engine)

    # 2. Synchronize Items Table (Add missing columns for 2.0.0)
    try:
        with engine.connect() as conn:
            with conn.begin():
                # PostgreSQL specific check and add
                sql = """
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='items' AND column_name='location_id') THEN
                        ALTER TABLE items ADD COLUMN location_id INTEGER REFERENCES locations(id);
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='items' AND column_name='supplier_id') THEN
                        ALTER TABLE items ADD COLUMN supplier_id INTEGER REFERENCES suppliers(id);
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='items' AND column_name='image_path') THEN
                        ALTER TABLE items ADD COLUMN image_path TEXT;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='items' AND column_name='description') THEN
                        ALTER TABLE items ADD COLUMN description TEXT;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='items' AND column_name='unit') THEN
                        ALTER TABLE items ADD COLUMN unit TEXT;
                    END IF;
                END $$;
                """
                conn.execute(text(sql))
                app_logger.info("Items table schema synchronized.")
    except Exception as e:
        app_logger.warning(f"Schema sync warning: {e}. This may be expected if not using PostgreSQL or if columns already exist.")

    # 3. Run manual schema additions (like devices)
    schema_path = os.path.join(os.path.dirname(__file__), "schema_devices.sql")
    if os.path.exists(schema_path):
        with open(schema_path, "r") as f:
            sql = f.read()
            with engine.connect() as conn:
                with conn.begin():
                    for statement in sql.split(";"):
                        if statement.strip():
                            conn.execute(text(statement))

    app_logger.info("Migration complete. System ready.")

if __name__ == "__main__":
    migrate()
