import pytest
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.user import Base, User
from services.auth_service import AuthService

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_auth_service_register_and_authenticate(db_session):
    service = AuthService(db_session)
    service.register({"username": "jules", "full_name": "Jules Engineer", "role": "admin", "password": "password123"})

    # Successful auth
    user = service.authenticate("jules", "password123")
    assert user is not None
    assert user.full_name == "Jules Engineer"

    # Failed auth (wrong pass)
    assert service.authenticate("jules", "wrong") is None

    # Failed auth (wrong user)
    assert service.authenticate("unknown", "password123") is None
