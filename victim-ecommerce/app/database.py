import asyncpg
import logging
from app.config import DATABASE_HOST, DATABASE_PORT, DATABASE_USER, DATABASE_PASSWORD, DATABASE_NAME, MAINTENANCE_DB

logger = logging.getLogger(__name__)

pool: asyncpg.Pool = None

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255),
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'customer',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    image_url VARCHAR(500),
    category VARCHAR(100),
    stock INT DEFAULT 100,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    total DECIMAL(10, 2),
    status VARCHAR(50) DEFAULT 'pending',
    shipping_address TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id) ON DELETE CASCADE,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS cart_items (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    quantity INT NOT NULL CHECK (quantity >= 1),
    UNIQUE (user_id, product_id)
);
"""

async def init_db():
    """Initialize database: create DB if not exists, create tables, set up connection pool."""
    global pool
    
    # Step 1: Connect to maintenance DB to create our database if needed
    try:
        sys_conn = await asyncpg.connect(
            host=DATABASE_HOST,
            port=DATABASE_PORT,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            database=MAINTENANCE_DB
        )
        
        # Check if database exists
        exists = await sys_conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", DATABASE_NAME
        )
        
        if not exists:
            # CREATE DATABASE cannot run inside a transaction
            await sys_conn.execute(f'CREATE DATABASE "{DATABASE_NAME}"')
            logger.info(f"Created database '{DATABASE_NAME}'")
        else:
            logger.info(f"Database '{DATABASE_NAME}' already exists")
            
        await sys_conn.close()
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise
    
    # Step 2: Create connection pool to our database
    pool = await asyncpg.create_pool(
        host=DATABASE_HOST,
        port=DATABASE_PORT,
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
        database=DATABASE_NAME,
        min_size=2,
        max_size=10
    )
    logger.info(f"Connection pool created for '{DATABASE_NAME}'")
    
    # Step 3: Create tables and apply additive migrations for existing databases
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA_SQL)
        await conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS stock INT DEFAULT 100")
        logger.info("Database schema initialized")


async def close_db():
    """Close the database connection pool."""
    global pool
    if pool:
        await pool.close()
        logger.info("Database connection pool closed")
