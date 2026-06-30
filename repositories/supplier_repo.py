from repositories.base_repository import BaseRepository
from models.inventory import Supplier
from sqlalchemy.orm import Session
from sqlalchemy import or_

class SupplierRepository(BaseRepository[Supplier]):
    def __init__(self, db: Session):
        super().__init__(Supplier, db)

    def search(self, term: str):
        return self.db.query(Supplier).filter(
            or_(
                Supplier.name.ilike(f"%{term}%"),
                Supplier.phone.ilike(f"%{term}%"),
                Supplier.email.ilike(f"%{term}%")
            ),
            Supplier.is_deleted == False
        ).all()
