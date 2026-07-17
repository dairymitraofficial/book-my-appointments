-- =========================================
-- DATABASE
-- =========================================
CREATE DATABASE IF NOT EXISTS book_my_appointments;
USE book_my_appointments;


-- =========================================
-- OWNERS
-- =========================================
CREATE TABLE owners (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE owner_profiles (
    owner_id INT PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    business_name VARCHAR(255) NOT NULL,

    building VARCHAR(100),
    area VARCHAR(150),
    post_office VARCHAR(100),
    district VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(6),

    address TEXT NOT NULL,
    description TEXT,
    profile_photo VARCHAR(255),

    FOREIGN KEY (owner_id) REFERENCES owners(id) ON DELETE CASCADE
);


-- =========================================
-- CUSTOMERS
-- =========================================
CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE customer_profiles (
    customer_id INT PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,

    building VARCHAR(100),
    area VARCHAR(150),
    post_office VARCHAR(100),
    district VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(6),

    address TEXT NOT NULL,
    profile_photo VARCHAR(255),

    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);


-- =========================================
-- OTP VERIFICATION
-- =========================================
CREATE TABLE otp_verifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    role ENUM('owner','customer') NOT NULL,
    otp_code VARCHAR(6) NOT NULL,
    attempts INT DEFAULT 0,
    expires_at DATETIME NOT NULL,
    locked_until DATETIME DEFAULT NULL
);


-- =========================================
-- CATEGORIES
-- =========================================
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE owner_categories (
    owner_id INT NOT NULL,
    category_id INT NOT NULL,
    PRIMARY KEY (owner_id, category_id),
    FOREIGN KEY (owner_id) REFERENCES owners(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);


-- =========================================
-- SERVICES
-- =========================================
CREATE TABLE services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id INT NOT NULL,

    service_name VARCHAR(255) NOT NULL,
    original_price DECIMAL(10,2) NOT NULL,
    price DECIMAL(10,2) NOT NULL,

    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (owner_id) REFERENCES owners(id) ON DELETE CASCADE
);

CREATE TABLE service_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_id INT NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    thumb_path VARCHAR(255),

    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE
);


-- =========================================
-- BOOKINGS
-- =========================================
CREATE TABLE bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,

    service_id INT NOT NULL,
    owner_id INT NOT NULL,
    customer_id INT NOT NULL,

    booking_date DATE NOT NULL,
    status ENUM('pending','accepted','rejected') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uniq_customer_service_date (customer_id, service_id, booking_date),

    FOREIGN KEY (service_id) REFERENCES services(id),
    FOREIGN KEY (owner_id) REFERENCES owners(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);


-- =========================================
-- CHAT SYSTEM
-- =========================================
CREATE TABLE conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id INT NOT NULL,
    customer_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uniq_owner_customer (owner_id, customer_id),

    FOREIGN KEY (owner_id) REFERENCES owners(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    sender ENUM('customer','owner') NOT NULL,
    message TEXT NOT NULL,

    delivered_at DATETIME NULL,
    seen_at DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);


-- =========================================
-- PUSH TOKENS
-- =========================================
CREATE TABLE push_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    role ENUM('customer','owner') NOT NULL,
    token TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uniq_user_role (user_id, role)
);


-- =========================================
-- USER PRESENCE
-- =========================================
CREATE TABLE user_presence (
    user_id INT NOT NULL,
    role ENUM('customer','owner') NOT NULL,
    last_seen DATETIME NOT NULL,
    PRIMARY KEY (user_id, role)
);


-- =========================================
-- EMAIL LOGS
-- =========================================
CREATE TABLE email_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255),
    purpose VARCHAR(100),
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================================
-- RATINGS
-- =========================================
CREATE TABLE ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stars INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================================
-- SOCIAL / FEED SYSTEM
-- =========================================
CREATE TABLE post_likes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    service_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY unique_like (customer_id, service_id),

    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE
);

CREATE TABLE customer_interests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    category_id INT NOT NULL,
    score INT DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY unique_interest (customer_id, category_id),

    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

CREATE TABLE service_views (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    service_id INT NOT NULL,
    viewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE
);


-- =========================================
-- ACTIVITY LOGS
-- =========================================
CREATE TABLE activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    role ENUM('customer','owner'),
    action VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================================
-- PERFORMANCE INDEXES
-- =========================================
CREATE INDEX idx_bookings_owner_date ON bookings(owner_id, booking_date);
CREATE INDEX idx_bookings_customer ON bookings(customer_id);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_created ON messages(conversation_id, created_at);

CREATE INDEX idx_services_owner ON services(owner_id);

CREATE INDEX idx_customer_interests_customer ON customer_interests(customer_id);
CREATE INDEX idx_service_views_customer ON service_views(customer_id);

CREATE INDEX idx_otp_email_role ON otp_verifications(email, role);

CREATE INDEX idx_user_presence_last_seen ON user_presence(last_seen);

CREATE INDEX idx_email_logs_email ON email_logs(email);

CREATE INDEX idx_conversations_customer ON conversations(customer_id);
CREATE INDEX idx_conversations_owner ON conversations(owner_id);

CREATE INDEX idx_service_images_service ON service_images(service_id);

CREATE INDEX idx_post_likes_service ON post_likes(service_id);


-- =========================================
-- DEFAULT CATEGORIES
-- =========================================
INSERT INTO categories (name) VALUES
('Mehndi Artist'),
('Makeup Artist'),
('Hairstylist'),
('Hairdresser'),
('Bridal Makeup'),
('Nail Artist'),
('Beautician'),
('Tattoo Artist'),
('Photographer'),
('Videographer'),
('Salon'),
('Beauty Parlour');

select * from owners;
