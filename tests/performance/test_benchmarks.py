import time
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.inventory import Base, Item
from repositories.item_user_repo import ItemRepository

def test_performance_bulk_insert():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    repo = ItemRepository(db)

    count = 10000
    start_time = time.time()

    items = [
        Item(code=f"ITM{i}", name=f"Product {i}", current_stock=i)
        for i in range(count)
    ]
    db.add_all(items)
    db.commit()

    end_time = time.time()
    duration = end_time - start_time
    print(f"\nBulk Insert of {count} items took: {duration:.4f}s")
    assert duration < 5.0 # Reasonable threshold for 10k in-memory

def test_performance_search():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    count = 10000
    items = [
        Item(code=f"ITM{i}", name=f"Product {i}", category="Electronics" if i % 2 == 0 else "Food")
        for i in range(count)
    ]
    db.add_all(items)
    db.commit()

    from services.item_service import ItemService
    service = ItemService(db)

    start_time = time.time()
    results = service.search_items("Product 999")
    end_time = time.time()

    duration = end_time - start_time
    print(f"Search in {count} items took: {duration:.4f}s")
    assert len(results) >= 1
    assert duration < 0.1
