"""
auth.py — Authentication routes
Endpoints: POST /api/auth/register, POST /api/login

Security note: /api/login contains an intentional SQL Injection vulnerability
(controlled by VULN_MODE env var) for the security demo pipeline.
"""
import logging
import jwt
from fastapi import APIRouter, HTTPException, Request

from app.database import pool
from app.config import VULN_MODE, JWT_SECRET, JWT_ALGORITHM
from app.models.schemas import UserRegister, UserLogin, LoginResponse, MessageResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/auth/register", response_model=MessageResponse)
async def register(data: UserRegister):
    """Register a new user. Passwords stored as plain text (intentional weakness)."""
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                "INSERT INTO users (username, email, password) VALUES ($1, $2, $3) RETURNING id",
                data.username, data.email, data.password
            )
            logger.info(f"New user registered: {data.username}")
            return MessageResponse(message=f"User registered successfully (id={row['id']})", success=True)
        except Exception as e:
            if "unique" in str(e).lower():
                raise HTTPException(status_code=400, detail="Username already exists")
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/login", response_model=LoginResponse)
async def login(data: UserLogin, request: Request):
    """
    Login endpoint.

    VULN_MODE=true  → Raw f-string SQL (SQL Injection target for the demo).
    VULN_MODE=false → Parameterized query (safe mode).
    """
    async with pool.acquire() as conn:
        row = None
        try:
            if VULN_MODE:
                # ── VULNERABLE PATH ────────────────────────────────────────────
                # Direct string interpolation allows payloads like:
                #   username: admin' OR '1'='1
                query = (
                    f"SELECT id, username, email, role FROM users "
                    f"WHERE username='{data.username}' AND password='{data.password}'"
                )
                row = await conn.fetchrow(query)
            else:
                # ── SAFE PATH ──────────────────────────────────────────────────
                row = await conn.fetchrow(
                    "SELECT id, username, email, role FROM users WHERE username=$1 AND password=$2",
                    data.username, data.password
                )
        except Exception as e:
            # Surface the DB error in the response so the demo can show the SQLi error message
            logger.warning(f"Login query error (may be SQLi attempt): {e}")
            raise HTTPException(status_code=400, detail=f"Database error: {e}")

        if not row:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = jwt.encode(
            {"user_id": row["id"], "username": row["username"], "role": row["role"]},
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )
        logger.info(f"User logged in: {row['username']}")
        return LoginResponse(
            token=token,
            user_id=row["id"],
            username=row["username"],
            role=row["role"],
        )
