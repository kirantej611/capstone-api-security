import logging
from app import database

logger = logging.getLogger(__name__)

async def seed_data():
    """Populate the database with demo data."""
    if not database.pool:
        logger.error("Database pool not initialized. Cannot seed data.")
        return

    async with database.pool.acquire() as conn:
        # Check if users table is empty
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        if user_count > 0:
            logger.info("Database already seeded. Skipping seed data insertion.")
            return
        
        logger.info("Seeding database with demo data...")
        
        # Seed users (plain text passwords for intentional vulnerability)
        await conn.executemany(
            "INSERT INTO users (username, email, password, role) VALUES ($1, $2, $3, $4)",
            [
                ("admin", "admin@store.com", "admin", "admin"),
                ("user1", "user1@store.com", "password123", "customer"),
                ("user2", "user2@store.com", "password456", "customer"),
            ]
        )
        logger.info("Seeded 3 users")
        
        # Seed products
        await conn.executemany(
            "INSERT INTO products (name, description, price, category, stock) VALUES ($1, $2, $3, $4, $5)",
            [
                ("Laptop Pro 15", "High-performance laptop with 16GB RAM", 1299.99, "electronics", 100),
                ("Wireless Mouse", "Ergonomic wireless mouse", 29.99, "electronics", 100),
                ("USB-C Hub", "7-in-1 USB-C hub adapter", 49.99, "electronics", 100),
                ("Mechanical Keyboard", "RGB mechanical gaming keyboard", 89.99, "electronics", 100),
                ("Classic T-Shirt", "100% cotton premium t-shirt", 24.99, "clothing", 100),
                ("Denim Jacket", "Vintage style denim jacket", 79.99, "clothing", 100),
                ("Running Shoes", "Lightweight running shoes", 119.99, "clothing", 100),
                ("Python Crash Course", "Learn Python programming", 39.99, "books", 100),
                ("Clean Code", "A handbook of agile software craftsmanship", 34.99, "books", 100),
                ("The Art of War", "Sun Tzu classic strategy", 12.99, "books", 100),
                ("Coffee Maker", "Programmable 12-cup coffee maker", 69.99, "home", 100),
                ("Desk Lamp", "LED desk lamp with USB charging", 44.99, "home", 100),
            ]
        )
        logger.info("Seeded 12 products")
        
        # Seed reviews
        await conn.executemany(
            "INSERT INTO reviews (product_id, user_id, rating, comment) VALUES ($1, $2, $3, $4)",
            [
                (1, 2, 5, "Amazing laptop, really fast!"),
                (2, 2, 4, "Good mouse but a bit small."),
                (5, 3, 5, "Fits perfectly, love the material."),
                (8, 3, 5, "Best book to learn Python."),
                (11, 2, 3, "Makes decent coffee, but a bit loud."),
            ]
        )
        logger.info("Seeded 5 reviews")
        
        # Seed orders
        await conn.executemany(
            "INSERT INTO orders (user_id, total, status, shipping_address) VALUES ($1, $2, $3, $4)",
            [
                (2, 1329.98, "delivered", "123 Main St, City"),
                (3, 114.98, "shipped", "456 Oak Ave, Town"),
            ]
        )
        logger.info("Seeded 2 orders")
        
        # Seed order items
        await conn.executemany(
            "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES ($1, $2, $3, $4)",
            [
                (1, 1, 1, 1299.99),
                (1, 2, 1, 29.99),
                (2, 6, 1, 79.99),
                (2, 9, 1, 34.99),
            ]
        )
        logger.info("Seeded 4 order items")
        
        logger.info("Database seeding completed successfully.")
