from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import get_db
from services.item_service import ItemService
from typing import List

app = FastAPI(title="Enterprise WMS API")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/items", response_model=List[dict])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    service = ItemService(db)
    items = service.get_items(skip=skip, limit=limit)
    return [{"code": i.code, "name": i.name, "stock": i.current_stock} for i in items]
