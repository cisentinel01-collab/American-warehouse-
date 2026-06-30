from typing import List, Optional
from models.user import User
from repositories.item_user_repo import UserRepository
from utils.auth import AuthManager
from app_logging.app_logger import app_logger
import bcrypt
from sqlalchemy.orm import Session

class AuthService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)
        self.db = db

    def authenticate(self, username, password) -> Optional[User]:
        user = self.user_repo.get_by_username(username)
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            if user.is_active:
                return user
        return None

    def register(self, user_data: dict) -> User:
        pwd = user_data.pop('password')
        hashed = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user_data['password_hash'] = hashed
        new_user = User(**user_data)
        return self.user_repo.create(new_user)

    def get_users(self) -> List[User]:
        return self.user_repo.get_all()

    def deactivate_user(self, user_id: int) -> bool:
        user = self.user_repo.get_by_id(user_id)
        if user:
            user.is_active = False
            self.db.commit()
            return True
        return False
