"""
Authentication middleware for Grammar-LLM-Bridge.
"""
import logging
from datetime import datetime
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.connection import async_session_maker
from app.db.api_keys import get_api_key_by_key, update_api_key_last_used
from app.db.users import get_user_by_id
from app.auth.utils import hash_api_key

logger = logging.getLogger("customlt")


async def api_key_auth_middleware(request: Request, call_next):
    """
    Middleware to validate API key from headers.

    Checks for X-API-Key header and validates it against database.
    Sets request.state.user if valid.
    """
    # Skip auth for public endpoints
    public_paths = ["/docs", "/openapi.json", "/redoc", "/health"]
    if request.url.path in public_paths:
        return await call_next(request)

    # Check for API key in headers or body (LT/Obsidian sends apiKey/username in form body)
    api_key = request.headers.get("X-API-Key")
    username = None

    # If no header, try to extract from body (form-urlencoded or JSON)
    if not api_key:
        try:
            raw_body = await request.body()
            body_str = raw_body.decode("utf-8", errors="ignore")
            content_type = request.headers.get("content-type", "")
            if "application/x-www-form-urlencoded" in content_type:
                parsed = parse_qs(body_str, keep_blank_values=True)
                api_key = (parsed.get("apiKey") or [None])[0]
                username = (parsed.get("username") or [None])[0]
            elif "application/json" in content_type:
                body_json = json.loads(body_str)
                if isinstance(body_json, dict):
                    api_key = body_json.get("apiKey") or body_json.get("api_key")
                    username = body_json.get("username") or body_json.get("email")
        except Exception:
            # Fail open: if parsing fails, proceed without user (backward compatibility)
            api_key = None

    if not api_key and username:
        logger.info("Received username without apiKey; treating as anonymous")

    if not api_key:
        # Allow requests without API key for now (backward compatibility)
        # In production, you might want to require API keys for all endpoints
        request.state.user = None
        return await call_next(request)

    # Validate API key
    async with async_session_maker() as db:
        hashed_key = hash_api_key(api_key)
        db_api_key = await get_api_key_by_key(db, hashed_key)

        if not db_api_key:
            logger.warning("Invalid API key attempt from %s", request.client.host)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid API key"}
            )

        if not db_api_key.is_active:
            logger.warning("Inactive API key used from %s", request.client.host)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "API key is inactive"}
            )

        if db_api_key.expires_at and db_api_key.expires_at < datetime.utcnow():
            logger.warning("Expired API key used from %s", request.client.host)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "API key has expired"}
            )

        # Get user
        user = await get_user_by_id(db, db_api_key.user_id)
        if not user or not user.is_active:
            logger.warning("API key for inactive user from %s", request.client.host)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "User account is inactive"}
            )

        # Update last_used_at (fire and forget)
        await update_api_key_last_used(db, db_api_key.id)
        await db.commit()

        # Set user in request state
        request.state.user = user
        request.state.api_key_id = db_api_key.id

    return await call_next(request)
