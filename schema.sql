CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(180) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(30) NOT NULL CHECK (
        role IN ('resident', 'secretary', 'watchman', 'admin')
    ),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS properties (
    id SERIAL PRIMARY KEY,
    title VARCHAR(180) NOT NULL,
    location VARCHAR(180) NOT NULL,
    property_type VARCHAR(50) NOT NULL,
    rent NUMERIC(12,2) NOT NULL,
    status VARCHAR(30) DEFAULT 'Available',
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS complaints (
    id SERIAL PRIMARY KEY,
    resident_id INT REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(180) NOT NULL,
    category VARCHAR(60) NOT NULL,
    description TEXT,
    status VARCHAR(40) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS amenities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    icon VARCHAR(10),
    description TEXT
);

CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    amenity_id INT REFERENCES amenities(id) ON DELETE CASCADE,
    booking_date DATE NOT NULL,
    slot VARCHAR(60) NOT NULL,
    status VARCHAR(30) DEFAULT 'Confirmed',
    UNIQUE (amenity_id, booking_date, slot)
);

CREATE TABLE IF NOT EXISTS visitors (
    id SERIAL PRIMARY KEY,
    visitor_name VARCHAR(120) NOT NULL,
    phone VARCHAR(40),
    purpose VARCHAR(160),
    visit_date DATE NOT NULL,
    status VARCHAR(30) DEFAULT 'Expected',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    resident_id INT REFERENCES users(id) ON DELETE CASCADE,
    amount NUMERIC(12,2) NOT NULL,
    payment_type VARCHAR(80) NOT NULL,
    due_date DATE,
    status VARCHAR(30) DEFAULT 'Pending'
);