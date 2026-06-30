from database.session import Session, engine
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app_logging.app_logger import app_logger

class DBManager:
    """Unified Database Manager using SQLAlchemy for connection pooling and ORM integration."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBManager, cls).__new__(cls)
        return cls._instance

    def execute_query(self, query, params=(), commit=False):
        """Enhanced Compatibility method for legacy raw SQL queries."""
        import re
        sql_converted = query
        param_dict = {}

        # 1. Robust Conversion of Positional (%s) to Named (:p1)
        if isinstance(params, (tuple, list)):
            def replace_placeholder(match):
                nonlocal count
                placeholder = f"p{count}"
                if (count-1) < len(params):
                    param_dict[placeholder] = params[count-1]
                count += 1
                return f":{placeholder}"

            count = 1
            # Regex to find %s that are not inside quotes or escaped
            # This is a simplified version but better than str.replace
            sql_converted = re.sub(r'(?<!%)%s', replace_placeholder, query)

            # If no %s was found but we have params (manual named params used)
            if not param_dict and len(params) > 0:
                for i, val in enumerate(params):
                    param_dict[f"p{i+1}"] = val

        elif isinstance(params, dict):
            param_dict = params

        try:
            with engine.connect() as conn:
                if commit:
                    with conn.begin():
                        result = conn.execute(text(sql_converted), param_dict)
                        if "RETURNING" in query.upper():
                            return result.scalar()
                        return None
                else:
                    result = conn.execute(text(sql_converted), param_dict)
                    if result.returns_rows:
                        return [dict(row._mapping) for row in result]
                    return []
        except SQLAlchemyError as e:
            app_logger.error(f"DBManager Query Error: {e} | SQL: {sql_converted} | Params: {param_dict}")
            raise e

    def get_session(self):
        return Session()
