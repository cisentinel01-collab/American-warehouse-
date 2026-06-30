from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from config.settings import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=30,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True
)

SessionFactory = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)
# scoped_session ensures that each thread has its own unique session
Session = scoped_session(SessionFactory)
Base = declarative_base()

def get_db():
    """Provides a transactional scope around a series of operations."""
    db = Session()
    try:
        yield db
    finally:
        Session.remove()
