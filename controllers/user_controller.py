from services.auth_service import AuthService
from sqlalchemy.orm import Session
from app_logging.app_logger import app_logger

class UserController:
    def __init__(self, db: Session):
        self.service = AuthService(db)

    def get_all_users(self):
        """Standardized method name for UserManagementView"""
        return self.service.get_users()

    def add_user(self, data):
        return self.service.register(data)

    def delete_user(self, user_id):
        return self.service.deactivate_user(user_id)
