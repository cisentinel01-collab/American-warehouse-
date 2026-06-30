import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.inventory import Base, Supplier
from repositories.supplier_repo import SupplierRepository

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_supplier_repo_create(db_session):
    repo = SupplierRepository(db_session)
    s = Supplier(name="S1", email="e1@test.com")
    repo.create(s)

    fetched = repo.get_all()
    assert len(fetched) == 1
    assert fetched[0].name == "S1"

def test_supplier_repo_search(db_session):
    repo = SupplierRepository(db_session)
    repo.create(Supplier(name="Apple Inc"))
    repo.create(Supplier(name="Microsoft"))

    results = repo.search("Apple")
    assert len(results) == 1
    assert results[0].name == "Apple Inc"
