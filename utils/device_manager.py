import socket
import uuid
from database.db_manager import DBManager
from sqlalchemy import text

def get_device_id():
    return str(uuid.getnode())

def get_computer_name():
    return socket.gethostname()

def register_device():
    db = DBManager()
    device_id = get_device_id()
    computer_name = get_computer_name()

    # Use %s as DBManager handles conversion to :param
    existing = db.execute_query(
        "SELECT * FROM devices WHERE device_id = %s",
        (device_id,)
    )

    if not existing:
        db.execute_query(
            "INSERT INTO devices(device_id, computer_name, status) VALUES (%s, %s, 'pending')",
            (device_id, computer_name),
            commit=True
        )

    return device_id

def check_device_status():
    db = DBManager()
    device_id = get_device_id()

    result = db.execute_query(
        "SELECT status, expiry_date FROM devices WHERE device_id = %s",
        (device_id,)
    )

    if not result:
        return False, "الجهاز غير مسجل"

    device = result[0]
    if device["status"] == "blocked":
        return False, "تم حظر هذا الجهاز"

    if device["status"] == "pending":
        return False, "يرجى التواصل مع المدير لتفعيل الجهاز"

    if device["expiry_date"] is not None:
        from datetime import date
        if isinstance(device["expiry_date"], str):
            from datetime import datetime
            try:
                expiry = datetime.strptime(device["expiry_date"], "%Y-%m-%d").date()
            except:
                expiry = date.today()
        else:
            expiry = device["expiry_date"]

        if expiry < date.today():
            return False, "انتهت صلاحية هذا الجهاز"

    return True, "OK"
