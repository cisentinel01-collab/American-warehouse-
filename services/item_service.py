from sqlalchemy.orm import Session
from repositories.item_user_repo import ItemRepository
from models.inventory import Item
from app_logging.app_logger import app_logger
from typing import List, Optional
from utils.signals import signal_manager

class ItemService:
    def __init__(self, db: Session):
        self.item_repo = ItemRepository(db)
        self.db = db

    def get_items(self, skip: int = 0, limit: int = 100) -> List[Item]:
        return self.item_repo.get_all(skip=skip, limit=limit)

    def create_item(self, item_data: dict) -> Item:
        # Handle manual 'unit' text mapping to uom_id or just use unit column
        # In our schema 'unit' is a TEXT column in items table.
        new_item = Item(**item_data)
        item = self.item_repo.create(new_item)
        app_logger.info(f"Item created: {item.code}")
        signal_manager.item_changed.emit()
        return item

    def update_stock(self, item_id: int, quantity_change: int):
        item = self.item_repo.get_by_id(item_id)
        if item:
            item.current_stock += quantity_change
            self.db.commit()
            if item.current_stock <= item.min_stock:
                app_logger.warning(f"Low stock alert for {item.code}: {item.current_stock}")
            return item
        return None

    def search_items(self, term: str, limit: int = 50, offset: int = 0) -> List[Item]:
        from sqlalchemy import or_
        from sqlalchemy.orm import joinedload
        return self.db.query(Item).options(
            joinedload(Item.uom),
            joinedload(Item.location),
            joinedload(Item.supplier)
        ).filter(
            or_(
                Item.name.ilike(f"%{term}%"),
                Item.code.ilike(f"%{term}%"),
                Item.category.ilike(f"%{term}%")
            ),
            Item.active == True
        ).offset(offset).limit(limit).all()

    def get_item_by_code(self, code: str) -> Optional[Item]:
        return self.item_repo.get_by_code(code)

    def get_item_by_id(self, item_id: int) -> Optional[Item]:
        return self.item_repo.get_by_id(item_id)

    def update_item(self, item_id: int, data: dict):
        item = self.item_repo.get_by_id(item_id)
        if item:
            return self.item_repo.update(item, data)
        return None

    def delete_item(self, item_id: int):
        return self.item_repo.delete(item_id)
