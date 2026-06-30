from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from database.session import Base

class Warehouse(Base):
    __tablename__ = "warehouses"
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    address = Column(Text)
    active = Column(Boolean, default=True)

    zones = relationship("Zone", back_populates="warehouse")

class Zone(Base):
    __tablename__ = "zones"
    id = Column(Integer, primary_key=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    code = Column(String(20), nullable=False, index=True)
    name = Column(String(100))

    warehouse = relationship("Warehouse", back_populates="zones")
    bins = relationship("Bin", back_populates="zone")

class Bin(Base):
    __tablename__ = "bins"
    id = Column(Integer, primary_key=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    code = Column(String(20), nullable=False, index=True)
    name = Column(String(100))

    zone = relationship("Zone", back_populates="bins")

class UnitOfMeasure(Base):
    __tablename__ = "uoms"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    category = Column(String(50)) # Unit, Weight, Volume
    type = Column(String(20)) # reference, bigger, smaller
    ratio = Column(Float, default=1.0) # ratio to reference unit in same category

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    barcode = Column(String(100), unique=True, index=True, nullable=True)
    name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), index=True)
    unit = Column(String(50)) # Manual text input
    uom_id = Column(Integer, ForeignKey("uoms.id"))
    location_id = Column(Integer, ForeignKey("locations.id"))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    tracking_type = Column(String(20), default="none") # none, serial, lot
    min_stock = Column(Float, default=0.0)
    current_stock = Column(Float, default=0.0)
    image_path = Column(String(500))
    description = Column(Text)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    uom = relationship("UnitOfMeasure")
    location = relationship("Location")
    supplier = relationship("Supplier")

class StockLot(Base):
    """Also known as Batch in the UI"""
    __tablename__ = "stock_lots"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    lot_number = Column(String(100), nullable=False, index=True)
    expiry_date = Column(Date, index=True)
    quantity = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("Item")

    @classmethod
    def get_expired(cls, session=None):
        from database.session import Session
        s = session or Session()
        return s.query(cls).filter(cls.expiry_date < datetime.utcnow().date(), cls.quantity > 0).all()

    @classmethod
    def get_expiring_soon(cls, months=6, session=None):
        from database.session import Session
        from datetime import timedelta
        s = session or Session()
        future_date = datetime.utcnow().date() + timedelta(days=months*30)
        return s.query(cls).filter(
            cls.expiry_date >= datetime.utcnow().date(),
            cls.expiry_date <= future_date,
            cls.quantity > 0
        ).all()

class StockQuant(Base):
    __tablename__ = "stock_quants"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    bin_id = Column(Integer, ForeignKey("bins.id"), nullable=False)
    lot_id = Column(Integer, ForeignKey("stock_lots.id"))
    quantity = Column(Float, default=0.0)

    item = relationship("Item")
    bin = relationship("Bin")
    lot = relationship("StockLot")

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(Text)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    active = Column(Boolean, default=True)

class Movement(Base):
    __tablename__ = "movements"
    id = Column(Integer, primary_key=True)
    type = Column(String(10), nullable=False)
    reference_no = Column(String(50), nullable=False, index=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    supplier = relationship("Supplier")
    received_by = Column(String(100))
    issuing_entity = Column(String(100))
    receiver_name = Column(String(100))
    notes = Column(Text)
    discount_percent = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    subtotal = Column(Float, default=0.0)
    final_total = Column(Float, default=0.0)

    items = relationship("MovementItem", back_populates="movement", cascade="all, delete-orphan")

class MovementItem(Base):
    __tablename__ = "movement_items"
    id = Column(Integer, primary_key=True)
    movement_id = Column(Integer, ForeignKey("movements.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, default=0.0)

    movement = relationship("Movement", back_populates="items")
    item = relationship("Item")

class Settings(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    company_name = Column(String(200), default="American Marine Services")
    logo_path = Column(String(500))
    address = Column(Text)
    phone = Column(String(50))
    email = Column(String(100))
    language = Column(String(10), default="ar")

# Aliases for backward compatibility or UI convenience
Batch = StockLot
