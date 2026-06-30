-- WMS Database Schema (ERP Upgrade - PostgreSQL)

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL, -- 'admin', 'warehouse_manager', 'follow_up'
    job_title TEXT,
    department TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers Table
CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    address TEXT,
    notes TEXT,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Warehouse Locations Table
CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE
);

-- Items Table
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    barcode TEXT UNIQUE,
    name TEXT NOT NULL,
    category TEXT,
    unit TEXT,
    location_id INTEGER REFERENCES locations(id),
    supplier_id INTEGER REFERENCES suppliers(id),
    min_stock REAL DEFAULT 0,
    current_stock REAL DEFAULT 0,
    image_path TEXT,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Batches Table
CREATE TABLE IF NOT EXISTS batches (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES items(id),
    batch_number TEXT NOT NULL,
    quantity REAL DEFAULT 0,
    production_date DATE,
    expiry_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stock Movements (In/Out)
CREATE TABLE IF NOT EXISTS movements (
    id SERIAL PRIMARY KEY,
    type TEXT NOT NULL, -- 'IN', 'OUT'
    reference_no TEXT NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    supplier_id INTEGER REFERENCES suppliers(id),
    received_by TEXT,
    issuing_entity TEXT,
    receiver_name TEXT,
    employee_name TEXT,
    reason TEXT,
    notes TEXT,
    discount_percent REAL DEFAULT 0,
    discount_amount REAL DEFAULT 0,
    subtotal REAL DEFAULT 0,
    final_total REAL DEFAULT 0
);

-- Movement Items (Details)
CREATE TABLE IF NOT EXISTS movement_items (
    id SERIAL PRIMARY KEY,
    movement_id INTEGER NOT NULL REFERENCES movements(id),
    item_id INTEGER NOT NULL REFERENCES items(id),
    batch_id INTEGER REFERENCES batches(id),
    quantity REAL NOT NULL,
    price REAL DEFAULT 0
);

-- Purchase Orders
CREATE TABLE IF NOT EXISTS purchase_orders (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    po_number TEXT UNIQUE NOT NULL,
    date DATE DEFAULT CURRENT_DATE,
    status TEXT DEFAULT 'pending',
    total REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Purchase Order Items
CREATE TABLE IF NOT EXISTS po_items (
    id SERIAL PRIMARY KEY,
    po_id INTEGER NOT NULL REFERENCES purchase_orders(id),
    item_id INTEGER NOT NULL REFERENCES items(id),
    quantity REAL NOT NULL,
    unit_price REAL DEFAULT 0,
    total REAL DEFAULT 0
);

-- Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    table_name TEXT,
    record_id INTEGER,
    details TEXT,
    old_value TEXT,
    new_value TEXT,
    device_name TEXT,
    ip_address TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Company Settings
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    company_name TEXT DEFAULT 'American Marine Services Free-Zone',
    logo_path TEXT,
    address TEXT,
    phone TEXT,
    email TEXT,
    language TEXT DEFAULT 'ar'
);

-- Initialize default settings
INSERT INTO settings (company_name)
SELECT 'American Marine Services Free-Zone'
WHERE NOT EXISTS (SELECT 1 FROM settings);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_items_code ON items(code);
CREATE INDEX IF NOT EXISTS idx_items_barcode ON items(barcode);
CREATE INDEX IF NOT EXISTS idx_items_name ON items(name);
CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);
CREATE INDEX IF NOT EXISTS idx_items_active ON items(active);
CREATE INDEX IF NOT EXISTS idx_items_created_at ON items(created_at);

CREATE INDEX IF NOT EXISTS idx_movements_type ON movements(type);
CREATE INDEX IF NOT EXISTS idx_movements_date ON movements(date);
CREATE INDEX IF NOT EXISTS idx_movements_ref ON movements(reference_no);

CREATE INDEX IF NOT EXISTS idx_batches_item_id ON batches(item_id);
CREATE INDEX IF NOT EXISTS idx_batches_expiry ON batches(expiry_date);

CREATE INDEX IF NOT EXISTS idx_mi_movement_id ON movement_items(movement_id);
CREATE INDEX IF NOT EXISTS idx_mi_item_id ON movement_items(item_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
