-- Manual database setup script for victim_ecommerce_db
-- CREATE DATABASE victim_ecommerce_db;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'customer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    image_url VARCHAR(255),
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    user_id INTEGER REFERENCES users(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    shipping_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);

INSERT INTO users (username, email, password, role) VALUES
('admin', 'admin@store.com', 'admin', 'admin'),
('user1', 'user1@store.com', 'password123', 'customer'),
('user2', 'user2@store.com', 'password456', 'customer');

INSERT INTO products (name, description, price, image_url, category) VALUES
('Laptop Pro 15', 'High-performance laptop with 16GB RAM and 512GB SSD', 1299.99, 'https://via.placeholder.com/300?text=Laptop', 'electronics'),
('Wireless Mouse', 'Ergonomic wireless mouse with long battery life', 29.99, 'https://via.placeholder.com/300?text=Mouse', 'electronics'),
('USB-C Hub', '7-in-1 USB-C hub adapter for modern laptops', 49.99, 'https://via.placeholder.com/300?text=USBHub', 'electronics'),
('Mechanical Keyboard', 'RGB mechanical gaming keyboard with Cherry MX switches', 89.99, 'https://via.placeholder.com/300?text=Keyboard', 'electronics'),
('Classic T-Shirt', '100% cotton premium t-shirt in various colors', 24.99, 'https://via.placeholder.com/300?text=TShirt', 'clothing'),
('Denim Jacket', 'Vintage style denim jacket with modern fit', 79.99, 'https://via.placeholder.com/300?text=Jacket', 'clothing'),
('Running Shoes', 'Lightweight running shoes with cushioned sole', 119.99, 'https://via.placeholder.com/300?text=Shoes', 'clothing'),
('Python Crash Course', 'Learn Python programming from beginner to advanced', 39.99, 'https://via.placeholder.com/300?text=Python', 'books'),
('Clean Code', 'A handbook of agile software craftsmanship by Robert C. Martin', 34.99, 'https://via.placeholder.com/300?text=CleanCode', 'books'),
('The Art of War', 'Sun Tzu classic strategy text with modern commentary', 12.99, 'https://via.placeholder.com/300?text=ArtOfWar', 'books'),
('Coffee Maker', 'Programmable 12-cup coffee maker with auto-shutoff', 69.99, 'https://via.placeholder.com/300?text=Coffee', 'home'),
('Desk Lamp', 'LED desk lamp with adjustable brightness and USB charging', 44.99, 'https://via.placeholder.com/300?text=Lamp', 'home');

INSERT INTO reviews (product_id, user_id, rating, comment) VALUES
(1, 2, 5, 'Excellent laptop! Great performance and battery life.'),
(1, 3, 4, 'Good laptop but a bit heavy for travel.'),
(5, 2, 5, 'Super comfortable, great quality cotton.'),
(8, 3, 5, 'Best Python book I have ever read. Highly recommended!'),
(4, 2, 4, 'Great keyboard, love the RGB lighting.');

INSERT INTO orders (user_id, total, status, shipping_address) VALUES
(2, 1329.98, 'completed', '456 Customer Ave, Tech Town'),
(3, 64.98, 'pending', '789 Shopper Ln, Buy City');

INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(1, 1, 1, 1299.99),
(1, 2, 1, 29.99),
(2, 5, 1, 24.99),
(2, 8, 1, 39.99);
