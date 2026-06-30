CREATE TABLE IF NOT EXISTS devices (
    id SERIAL PRIMARY KEY,
    device_id TEXT UNIQUE NOT NULL,
    computer_name TEXT,
    status TEXT DEFAULT 'pending',
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expiry_date DATE
);
