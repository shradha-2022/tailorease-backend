-- Create database
CREATE DATABASE tailorease;

-- Connect to database
\c tailorease;

-- Create tables
CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    city VARCHAR(50) NOT NULL,
    address TEXT NOT NULL,
    garment_type VARCHAR(50) NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    preferred_date DATE NOT NULL,
    time_slot VARCHAR(20) NOT NULL,
    special_instructions TEXT,
    payment_method VARCHAR(30) DEFAULT 'UPI / Online',
    status VARCHAR(50) DEFAULT 'Booking Confirmed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_status (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) REFERENCES bookings(order_id) ON DELETE CASCADE,
    status_label VARCHAR(100) NOT NULL,
    status_time TIMESTAMP,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contact_messages (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_bookings_order_id ON bookings(order_id);
CREATE INDEX idx_bookings_phone ON bookings(phone);
CREATE INDEX idx_order_status_order_id ON order_status(order_id);
CREATE INDEX idx_contact_messages_created_at ON contact_messages(created_at);