from models.user import User
from models.inventory import Supplier
from models.inventory import Item
from models.inventory import Location
from database.db_manager import DBManager
import bcrypt

from database.session import Session

def seed_data():
    db_session = Session()
    db_manager = DBManager()

    # 1. Users - Two Roles Only
    users = [
        {"username": "manager", "password": "123", "full_name": "مسؤول المخزن", "role": "warehouse_manager"},
        {"username": "followup", "password": "123", "full_name": "المتابعة", "role": "follow_up"}
    ]
    for u in users:
        if not db_manager.execute_query("SELECT id FROM users WHERE username = %s", (u['username'],)):
            password_hash = bcrypt.hashpw(u['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            new_user = User(
                username=u['username'],
                password_hash=password_hash,
                full_name=u['full_name'],
                role=u['role']
            )
            db_session.add(new_user)

    # 2. Scale Up Locations (100 Locations)
    existing_locs = db_manager.execute_query("SELECT name FROM locations")
    existing_loc_names = [r['name'] for r in existing_locs]

    for i in range(1, 101):
        name = f"Location-Zone-{i:03d}"
        if name not in existing_loc_names:
            db_session.add(Location(name=name, description=f"Automated Enterprise Bin {i}"))

    # 3. Scale Up Suppliers (70 Suppliers)
    existing_sups = db_manager.execute_query("SELECT name FROM suppliers")
    existing_sup_names = [r['name'] for r in existing_sups]

    for i in range(1, 71):
        name = f"Strategic-Supplier-{i:03d}"
        if name not in existing_sup_names:
            db_session.add(Supplier(
                name=name,
                phone=f"050-900-{i:03d}",
                email=f"vendor{i}@enterprise.com",
                address=f"Industrial Area Block {i}"
            ))

    db_session.commit()

    # 4. Scale Up Items (600 Items)
    existing_items = db_manager.execute_query("SELECT code FROM items")
    existing_codes = [r['code'] for r in existing_items]

    for i in range(1, 601):
        code = f"SKU-AMS-{i:04d}"
        if code not in existing_codes:
            db_session.add(Item(
                code=code,
                name=f"High-Performance Component {i}",
                category="Hardware" if i % 2 == 0 else "Electronic",
                unit="PCS",
                min_stock=20.0,
                current_stock=100.0,
                active=True
            ))

    db_session.commit()

    # 5. Generate Sample Movements (Invoices)
    from models.inventory import Movement, MovementItem
    import random
    from datetime import datetime, timedelta

    all_items = db_session.query(Item).all()
    all_suppliers = db_session.query(Supplier).all()

    if all_items and all_suppliers:
        for i in range(1, 21): # More movements for better charts
            m_type = 'IN' if i % 2 == 0 else 'OUT'
            ref = f"{m_type}-BATCH-{i:03d}"

            m = Movement(
                type=m_type,
                reference_no=ref,
                date=datetime.now() - timedelta(days=random.randint(0, 30)),
                supplier_id=random.choice(all_suppliers).id if m_type == 'IN' else None,
                issuing_entity="SEED-DEPT" if m_type == 'OUT' else None,
                subtotal=0,
                final_total=0
            )
            db_session.add(m)
            db_session.flush()

            total = 0
            for _ in range(random.randint(1, 8)):
                it = random.choice(all_items)
                qty = random.randint(1, 50)
                price = random.uniform(10, 500)
                mi = MovementItem(movement_id=m.id, item_id=it.id, quantity=qty, price=price)
                db_session.add(mi)
                total += (qty * price)

            m.subtotal = total
            m.final_total = total

    db_session.commit()
    db_session.close()

    print("Data seeding completed: 2 Users, 100 Locations, 70 Suppliers, 600 Items, 10 Movements.")

if __name__ == "__main__":
    seed_data()
