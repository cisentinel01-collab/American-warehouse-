from repositories.base_repository import BaseRepository
from models.inventory import Warehouse, UnitOfMeasure
from sqlalchemy.orm import Session

class WarehouseRepository(BaseRepository[Warehouse]):
    def __init__(self, db: Session):
        super().__init__(Warehouse, db)

class UOMRepository(BaseRepository[UnitOfMeasure]):
    def __init__(self, db: Session):
        super().__init__(UnitOfMeasure, db)
