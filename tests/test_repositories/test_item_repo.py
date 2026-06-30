import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.inventory import Base, Item
from repositories.item_user_repo import ItemRepository

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_item_repo_create(db_session):
    repo = ItemRepository(db_session)
    item = Item(code="C1", name="N1")
    repo.create(item)

    fetched = repo.get_by_code("C1")
    assert fetched.name == "N1"

def test_item_repo_get_by_any(db_session):
    repo = ItemRepository(db_session)
    item = Item(code="C2", barcode="B2", name="N2")
    repo.create(item)

    assert repo.get_by_any_identifier("C2").name == "N2"
    assert repo.get_by_any_identifier("B2").name == "N2"
