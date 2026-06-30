import pytest
from models.inventory import Item, Supplier
from models.user import User

def test_new_user():
    user = User(username="testuser", full_name="Test User", role="admin")
    assert user.username == "testuser"
    assert user.role == "admin"
    assert user.is_active is True

def test_new_item():
    item = Item(code="ITM001", name="Test Item", current_stock=10.5)
    assert item.code == "ITM001"
    assert item.current_stock == 10.5

def test_new_supplier():
    s = Supplier(name="Supp1", email="supp1@example.com")
    assert s.name == "Supp1"
    assert s.email == "supp1@example.com"
