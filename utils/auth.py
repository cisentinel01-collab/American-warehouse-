class AuthManager:
    _current_user = None

    @classmethod
    def login(cls, username, password):
        from database.session import Session
        from services.auth_service import AuthService

        db = Session()
        try:
            auth_service = AuthService(db)
            user = auth_service.authenticate(username, password)
            if user:
                # Store user as dict to keep it serializable and avoid session detached errors
                cls._current_user = {
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.full_name,
                    'role': user.role
                }
                return True
            return False
        finally:
            db.close()

    @classmethod
    def get_current_user(cls):
        return cls._current_user

    @classmethod
    def logout(cls):
        cls._current_user = None

    @classmethod
    def has_permission(cls, module, action=None):
        if not cls._current_user:
            return False

        role = cls._current_user['role']

        # 1. Admin: Full Access to everything including 'users'
        if role == 'admin':
            return True

        # 2. مسئول المخزن (Full access except Users and Settings)
        if role == 'warehouse_manager':
            if module in ['users', 'settings']:
                return False
            return True

        # 3. المتابعة (Strict View Only)
        if role == 'follow_up':
            # Block any action that modifies data
            if action in ['add', 'edit', 'delete', 'submit', 'save', 'create', 'can_edit']:
                return False
            # Allow viewing core modules
            if module in ['dashboard', 'reports', 'items', 'suppliers', 'locations', 'stock_in', 'stock_out', 'purchase']:
                return True
            return False

        return False
