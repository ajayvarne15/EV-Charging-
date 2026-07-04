CREATE DATABASE IF NOT EXISTS ev_charging_db;
USE ev_charging_db;

DROP TABLE IF EXISTS charging_sessions;
DROP TABLE IF EXISTS vehicles;
DROP TABLE IF EXISTS pricing;
DROP TABLE IF EXISTS admin_users;
DROP TABLE IF EXISTS station_settings;

CREATE TABLE vehicles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    vehicle_name VARCHAR(100) NOT NULL,
    vehicle_id VARCHAR(100) NOT NULL UNIQUE,
    owner_name VARCHAR(100),
    mobile_number VARCHAR(20),
    battery_capacity DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pricing (
    id INT PRIMARY KEY AUTO_INCREMENT,
    price_per_unit DECIMAL(10,2) NOT NULL DEFAULT 12.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO pricing (price_per_unit) VALUES (12.00);

CREATE TABLE station_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    station_name VARCHAR(150) NOT NULL DEFAULT 'EV Smart Charge Station',
    station_location VARCHAR(200) DEFAULT 'Warangal, Telangana',
    support_number VARCHAR(20) DEFAULT '9876543210',
    gst_number VARCHAR(50) DEFAULT 'EV-DEMO-001',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO station_settings (station_name, station_location, support_number, gst_number)
VALUES ('EV Smart Charge Station', 'Warangal, Telangana', '9876543210', 'EV-DEMO-001');

CREATE TABLE charging_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    vehicle_id INT NOT NULL,
    vehicle_name VARCHAR(100) NOT NULL,
    battery_capacity DECIMAL(10,2) NOT NULL,
    start_battery_percent DECIMAL(10,2) NOT NULL,
    current_battery_percent DECIMAL(10,2) NOT NULL,
    target_battery_percent DECIMAL(10,2) NOT NULL,
    charger_power DECIMAL(10,2) NOT NULL,
    price_per_unit DECIMAL(10,2) NOT NULL,

    current_energy DECIMAL(10,4) NOT NULL DEFAULT 0,
    target_energy DECIMAL(10,4) NOT NULL DEFAULT 0,
    units_required DECIMAL(10,4) NOT NULL DEFAULT 0,
    units_consumed DECIMAL(10,4) NOT NULL DEFAULT 0,
    units_left DECIMAL(10,4) NOT NULL DEFAULT 0,

    amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    estimated_total_hours DECIMAL(10,4) NOT NULL DEFAULT 0,
    time_left_hours DECIMAL(10,4) NOT NULL DEFAULT 0,
    total_duration_seconds INT NOT NULL DEFAULT 0,

    status ENUM('Charging', 'Full', 'Stopped') DEFAULT 'Charging',

    start_time DATETIME NOT NULL,
    end_time DATETIME NULL,
    last_updated DATETIME NOT NULL,

    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
);

CREATE TABLE admin_users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO admin_users (username, password)
VALUES ('admin', 'admin123');

-- Optional sample vehicles
INSERT INTO vehicles (vehicle_name, vehicle_id, owner_name, mobile_number, battery_capacity)
VALUES
('Tata Nexon EV', 'EV-1001', 'Rahul', '9000000001', 50.00),
('MG ZS EV', 'EV-1002', 'Kiran', '9000000002', 44.50),
('BYD Atto 3', 'EV-1003', 'Anil', '9000000003', 60.00);