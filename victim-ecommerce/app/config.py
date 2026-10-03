import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = int(os.getenv("DATABASE_PORT", "5432"))
DATABASE_USER = os.getenv("DATABASE_USER", "admin")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "password")
DATABASE_NAME = os.getenv("DATABASE_NAME", "victim_ecommerce_db")
MAINTENANCE_DB = os.getenv("MAINTENANCE_DB", "postgres")

# JWT Configuration (intentionally weak secret for demo)
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-123")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Vulnerability toggle: when True, intentional vulnerabilities are active
# Set to 'false' to demonstrate secure mode
VULN_MODE = os.getenv("VULN_MODE", "true").lower() == "true"

# File upload directory
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"))
