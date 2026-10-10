"""Client-safe HTTP errors; internal details stay in logs."""
import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def raise_client_error(status_code: int, detail: str) -> None:
    raise HTTPException(status_code=status_code, detail=detail)


def raise_internal_error(exc: Exception, public_detail: str = "Internal server error") -> None:
    logger.exception("Internal error: %s", exc)
    raise HTTPException(status_code=500, detail=public_detail)
