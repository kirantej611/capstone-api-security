import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db, close_db
from app.seed import seed_data
from app.middleware.logging_middleware import LoggingMiddleware

# Import routers
from app.routes.auth import router as auth_router
from app.routes.products import router as products_router
from app.routes.reviews import router as reviews_router
from app.routes.cart import router as cart_router
from app.routes.orders import router as orders_router
from app.routes.user import router as user_router
from app.routes.vulnerable import router as vulnerable_router

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("SKIP_DB_INIT") == "1":
        yield
        return
    await init_db()
    await seed_data()
    yield
    await close_db()

app = FastAPI(
    title="Victim E-Commerce API",
    description="Intentionally vulnerable e-commerce backend for security demo",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware allowing ALL origins (intentional vulnerability)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)

# Include all route routers
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(reviews_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(user_router)
app.include_router(vulnerable_router)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "victim-ecommerce", "version": "1.0.0"}
