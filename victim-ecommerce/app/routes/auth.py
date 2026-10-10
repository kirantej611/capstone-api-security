"""
auth.py — Authentication routes
Endpoints: POST /api/auth/register, POST /api/login

Security note: /api/login contains an intentional SQL Injection vulnerability
(controlled by VULN_MODE env var) for the security demo pipeline.
"""
import logging

import asyncpg
import jwt
from fastapi import APIRouter, HTTPException

from app import database
from app.config import JWT_ALGORITHM, JWT_SECRET, VULN_MODE
from app.errors import raise_internal_error
from app.models.schemas import LoginResponse, MessageResponse, UserLogin, UserRegister

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/auth/register", response_model=MessageResponse, status_code=201)
async def register(data: UserRegister):
    """Register a new user. Passwords stored as plain text (intentional weakness)."""
    async with database.pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                "INSERT INTO users (username, email, password) VALUES ($1, $2, $3) RETURNING id",
                data.username,
                data.email,
                data.password,
            )
            logger.info("New user registered: %s", data.username)
            return MessageResponse(
                message=f"User registered successfully (id={row['id']})",
                success=True,
            )
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail="Username or email already exists")
        except Exception as exc:
            raise_internal_error(exc, "Registration failed")


@router.post("/api/login", response_model=LoginResponse)
async def login(data: UserLogin):
    """
    Login endpoint.

    VULN_MODE=true  → Raw f-string SQL (SQL Injection target for the demo).
    VULN_MODE=false → Parameterized query (safe mode).
    """
    async with database.pool.acquire() as conn:
        row = None
        try:
            if VULN_MODE:
                # ── VULNERABLE PATH ────────────────────────────────────────────
                query = (
                    f"SELECT id, username, email, role FROM users "
                    f"WHERE username='{data.username}' AND password='{data.password}'"
                )
                row = await conn.fetchrow(query)
            else:
                row = await conn.fetchrow(
                    "SELECT id, username, email, role FROM users WHERE username=$1 AND password=$2",
                    data.username,
                    data.password,
                )
        except Exception as exc:
            logger.warning("Login query error (may be SQLi attempt): %s", exc)
            if VULN_MODE:
                raise HTTPException(status_code=400, detail=f"Database error: {exc}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not row:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = jwt.encode(
            {"user_id": row["id"], "username": row["username"], "role": row["role"]},
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )
        logger.info("User logged in: %s", row["username"])
        return LoginResponse(
            token=token,
            user_id=row["id"],
            username=row["username"],
            role=row["role"],
        )
