import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.inventory import Base, Item
from services.item_service import ItemService
import os

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_item_service_create_and_search(db_session):
    service = ItemService(db_session)
    service.create_item({"code": "CODE1", "name": "Test Product", "category": "Test"})

    results = service.search_items("Product")
    assert len(results) == 1
    assert results[0].code == "CODE1"

def test_item_service_stock_update(db_session):
    service = ItemService(db_session)
    item = service.create_item({"code": "S1", "name": "Stock Item", "current_stock": 10})

    service.update_stock(item.id, 5)
    assert item.current_stock == 15

    service.update_stock(item.id, -20)
    assert item.current_stock == -5
