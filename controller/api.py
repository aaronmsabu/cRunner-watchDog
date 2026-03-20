"""
FastAPI control API for the Runner Watchdog.

Endpoints let you inspect fleet state, check for updates, and manually
trigger rolling replacements.

All routes except /health require API key authentication via the
X-API-Key header.
"""

import logging
import secrets
import threading
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

from controller.config import RUNNER_VERSION, WATCHDOG_API_KEY
from controller.github_api import get_latest_runner_version, get_repo_runners
from controller.main import fleet_controller, run_watchdog
from controller.runner_manager import rolling_update
from controller.version_checker import check_for_upgrade, get_outdated_runners
from database.redis_client import get_all_runners

logger = logging.getLogger("watchdog.api")


# ── API Key authentication ──────────────────────────────────────────────────

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def _verify_api_key(
    api_key: str | None = Security(_api_key_header),
) -> str:
    """
    Validate the X-API-Key header against the configured WATCHDOG_API_KEY.

    Uses constant-time comparison to prevent timing attacks.
    """
    if not WATCHDOG_API_KEY:
        # If no key is configured, reject all requests (fail-closed)
        logger.error("WATCHDOG_API_KEY is not set — rejecting request")
        raise HTTPException(status_code=503, detail="API key not configured on server")

    if api_key is None:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    if not secrets.compare_digest(api_key, WATCHDOG_API_KEY):
        raise HTTPException(status_code=403, detail="Invalid API key")

    return api_key


# ── Lifespan: start the background watchdog loop ────────────────────────────

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Start the watchdog loop in a background daemon thread on startup."""
    thread = threading.Thread(target=run_watchdog, daemon=True)
    thread.start()
    logger.info("Background watchdog thread started")
    yield


app = FastAPI(
    title="Runner Watchdog API",
    description="Control plane for the self-hosted GitHub Actions runner fleet.",
    version="0.1.0",
    lifespan=lifespan,
)


# ── Public endpoints (no auth) ──────────────────────────────────────────────

@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness check — no authentication required."""
    return {"status": "ok"}


# ── Protected endpoints (require X-API-Key) ─────────────────────────────────

@app.get("/runners", dependencies=[Depends(_verify_api_key)])
async def list_runners() -> dict[str, Any]:
    """List all runners from the local registry."""
    runners = get_all_runners()
    return {"count": len(runners), "runners": runners}


@app.get("/runners/github", dependencies=[Depends(_verify_api_key)])
async def list_github_runners() -> dict[str, Any]:
    """List runners registered on GitHub for the configured repo."""
    try:
        runners = get_repo_runners()
        return {"count": len(runners), "runners": runners}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/version/latest", dependencies=[Depends(_verify_api_key)])
async def latest_version() -> dict[str, str]:
    """Fetch the latest runner version from GitHub."""
    try:
        version = get_latest_runner_version()
        return {"latest_version": version}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/status", dependencies=[Depends(_verify_api_key)])
async def fleet_status() -> dict[str, Any]:
    """Fleet status summary: counts by version and upgrade availability."""
    runners = get_all_runners()

    version_counts: dict[str, int] = {}
    for data in runners.values():
        v = data.get("version", "unknown")
        version_counts[v] = version_counts.get(v, 0) + 1

    try:
        needs_upgrade, latest = check_for_upgrade()
    except Exception:
        needs_upgrade, latest = None, "unavailable"

    return {
        "total_runners": len(runners),
        "baseline_version": RUNNER_VERSION,
        "latest_version": latest,
        "upgrade_available": needs_upgrade,
        "version_distribution": version_counts,
    }


@app.post("/check-update", dependencies=[Depends(_verify_api_key)])
async def trigger_check() -> dict[str, Any]:
    """Manually trigger a version check."""
    try:
        needs_upgrade, latest = check_for_upgrade()
        return {
            "upgrade_available": needs_upgrade,
            "latest_version": latest,
            "current_version": RUNNER_VERSION,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/trigger-update", dependencies=[Depends(_verify_api_key)])
async def trigger_update() -> JSONResponse:
    """Manually trigger a rolling update if an upgrade is available."""
    try:
        needs_upgrade, latest = check_for_upgrade()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not needs_upgrade:
        return JSONResponse(
            status_code=200,
            content={"message": "Fleet is already up-to-date", "version": latest},
        )

    outdated = get_outdated_runners(latest)
    if not outdated:
        return JSONResponse(
            status_code=200,
            content={"message": "No outdated runners found in registry"},
        )

    summary = rolling_update(outdated, latest)
    return JSONResponse(status_code=200, content=summary)
