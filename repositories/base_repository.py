from typing import Generic, TypeVar, Type, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database.session import Base
from app_logging.app_logger import app_logger

T = TypeVar("T", bound=Base)

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: int) -> Optional[T]:
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            app_logger.error(f"Error fetching {self.model.__name__} by id {id}: {e}")
            self.db.rollback()
            raise

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        try:
            return self.db.query(self.model).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            app_logger.error(f"Error fetching all {self.model.__name__}: {e}")
            self.db.rollback()
            raise

    def create(self, obj_in: T) -> T:
        try:
            self.db.add(obj_in)
            self.db.commit()
            self.db.refresh(obj_in)
            return obj_in
        except SQLAlchemyError as e:
            self.db.rollback()
            app_logger.error(f"Error creating {self.model.__name__}: {e}")
            raise

    def update(self, db_obj: T, obj_in: dict) -> T:
        try:
            for field, value in obj_in.items():
                setattr(db_obj, field, value)
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            app_logger.error(f"Error updating {self.model.__name__} {db_obj.id}: {e}")
            raise

    def delete(self, id: int) -> bool:
        try:
            db_obj = self.get_by_id(id)
            if db_obj:
                self.db.delete(db_obj)
                self.db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            app_logger.error(f"Error deleting {self.model.__name__} {id}: {e}")
            raise
