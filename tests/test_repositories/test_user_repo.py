import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.user import User
from repositories.item_user_repo import UserRepository

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    from database.session import Base
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_user_repo_create(db_session):
    repo = UserRepository(db_session)
    user = User(username="admin", full_name="Admin User", role="admin", password_hash="hash")
    repo.create(user)

    fetched = repo.get_by_username("admin")
    assert fetched.full_name == "Admin User"

def test_user_repo_get_all(db_session):
    repo = UserRepository(db_session)
    repo.create(User(username="u1", full_name="User 1", role="manager", password_hash="h1"))
    repo.create(User(username="u2", full_name="User 2", role="follow_up", password_hash="h2"))

    users = repo.get_all()
    assert len(users) == 2
