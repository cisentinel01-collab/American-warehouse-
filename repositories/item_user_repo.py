from repositories.base_repository import BaseRepository
from models.inventory import Item
from models.user import User
from sqlalchemy.orm import Session, joinedload

class ItemRepository(BaseRepository[Item]):
    def __init__(self, db: Session):
        super().__init__(Item, db)

    def get_all(self, skip: int = 0, limit: int = 100):
        # Eager load relationships to prevent DetachedInstanceError in async UI
        return self.db.query(Item).options(
            joinedload(Item.uom),
            joinedload(Item.location),
            joinedload(Item.supplier)
        ).offset(skip).limit(limit).all()

    def get_by_code(self, code: str) -> Item:
        return self.db.query(Item).options(
            joinedload(Item.uom),
            joinedload(Item.location),
            joinedload(Item.supplier)
        ).filter(Item.code == code).first()

    def get_by_barcode(self, barcode: str) -> Item:
        return self.db.query(Item).filter(Item.barcode == barcode).first()

    def get_by_any_identifier(self, identifier: str) -> Item:
        """Search by code or barcode."""
        return self.db.query(Item).filter(
            (Item.code == identifier) | (Item.barcode == identifier)
        ).first()

    def get_low_stock(self) -> list[Item]:
        return self.db.query(Item).filter(Item.current_stock <= Item.min_stock, Item.active == True).all()

    def create(self, item: Item) -> Item:
        try:
            # Upsert Logic: Check if code exists
            existing = self.get_by_code(item.code)
            if existing:
                existing.name = item.name
                existing.category = item.category
                existing.unit = item.unit
                existing.min_stock = item.min_stock
                # For opening balance/imports, we might update current_stock
                if item.current_stock > 0:
                    existing.current_stock = item.current_stock
                self.db.commit()
                self.db.refresh(existing)
                return existing

            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return item
        except Exception as e:
            self.db.rollback()
            raise e

class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_username(self, username: str) -> User:
        return self.db.query(User).filter(User.username == username).first()
