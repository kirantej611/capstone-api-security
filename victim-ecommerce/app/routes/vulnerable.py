"""
vulnerable.py — Intentionally vulnerable demo endpoints
Endpoints:
  GET  /api/download?file=  — Path Traversal (VULN_MODE controls sanitization)
  POST /api/ping            — Command Injection (VULN_MODE controls sanitization)

These endpoints exist specifically so the ML engine can demonstrate detection of
path_traversal and command_injection attack categories in the live demo.
"""
import os
import re
import platform
import subprocess
import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.config import VULN_MODE, UPLOAD_DIR
from app.models.schemas import PingRequest, PingResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/download", response_class=PlainTextResponse)
async def download_file(file: str = Query(..., description="File name to download")):
    """
    Download a file from the uploads directory.

    VULN_MODE=true  → path is NOT sanitized, allowing ../../ traversal.
    VULN_MODE=false → resolves real path and blocks anything outside UPLOAD_DIR.
    """
    if VULN_MODE:
        # ── VULNERABLE PATH ────────────────────────────────────────────────────
        # No canonicalization — e.g. file=../../etc/passwd reads system files
        filepath = os.path.join(UPLOAD_DIR, file)
        try:
            with open(filepath, "r", errors="replace") as f:
                content = f.read()
            logger.warning(f"[PATH_TRAVERSAL] File accessed: {filepath}")
            return content
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"File not found: {file}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # ── SAFE PATH ──────────────────────────────────────────────────────────
        base = os.path.realpath(UPLOAD_DIR)
        filepath = os.path.realpath(os.path.join(UPLOAD_DIR, file))
        if not filepath.startswith(base + os.sep) and filepath != base:
            raise HTTPException(status_code=403, detail="Access denied: path outside upload directory")
        try:
            with open(filepath, "r", errors="replace") as f:
                content = f.read()
            return content
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="File not found")


@router.post("/api/ping", response_model=PingResponse)
async def ping_host(data: PingRequest):
    """
    Ping a host — admin diagnostic endpoint.

    VULN_MODE=true  → host string passed directly to shell (Command Injection).
                       e.g. host="127.0.0.1; whoami" executes both commands.
    VULN_MODE=false → host validated against safe pattern; run without shell=True.
    """
    is_windows = platform.system().lower() == "windows"
    count_flag = "-n" if is_windows else "-c"

    try:
        if VULN_MODE:
            # ── VULNERABLE PATH ────────────────────────────────────────────────
            # shell=True + unsanitized input = command injection
            cmd = f"ping {count_flag} 1 {data.host}"
            logger.warning(f"[CMD_INJECTION] Executing: {cmd}")
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=10
            )
        else:
            # ── SAFE PATH ──────────────────────────────────────────────────────
            if not re.match(r"^[a-zA-Z0-9.\-]{1,253}$", data.host):
                raise HTTPException(status_code=400, detail="Invalid hostname or IP address")
            result = subprocess.run(
                ["ping", count_flag, "1", data.host],
                capture_output=True, text=True, timeout=10
            )

        output = (result.stdout or "") + (result.stderr or "")
        return PingResponse(host=data.host, output=output, success=result.returncode == 0)

    except subprocess.TimeoutExpired:
        return PingResponse(host=data.host, output="Request timed out", success=False)
    except HTTPException:
        raise
    except Exception as e:
        return PingResponse(host=data.host, output=str(e), success=False)
