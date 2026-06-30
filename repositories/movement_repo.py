from repositories.base_repository import BaseRepository
from models.inventory import Movement
from sqlalchemy.orm import Session

class MovementRepository(BaseRepository[Movement]):
    def __init__(self, db: Session):
        super().__init__(Movement, db)

    def get_history(self, type=None, limit=100, offset=0):
        from sqlalchemy.orm import joinedload
        query = self.db.query(Movement).options(joinedload(Movement.supplier))
        if type:
            query = query.filter(Movement.type == type)
        return query.order_by(Movement.date.desc()).offset(offset).limit(limit).all()
