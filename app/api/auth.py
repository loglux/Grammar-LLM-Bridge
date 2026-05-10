"""
Authentication endpoints.
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.db import get_db
from app.db.users import create_user, get_user_by_username, get_user_by_email
from app.db.api_keys import create_api_key, get_user_api_keys, revoke_api_key
from app.auth import (
    get_current_user,
    hash_password,
    verify_password,
    generate_api_key,
    hash_api_key
)
from app.auth.rate_limiter import rate_limiter
from app.models.auth import (
    User,
    UserCreate,
    UserResponse,
    APIKeyCreate,
    APIKeyResponse
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("customlt")


class LoginRequest(BaseModel):
    """Login credentials."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response with API key."""
    api_key: str
    user: UserResponse
    message: str


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login and receive an API key for subsequent requests.

    TEMPORARY SOLUTION: Returns a session API key (expires in 30 days).
    Future: Can be extended to JWT, OAuth2, or other auth mechanisms.
    """
    # Verify credentials
    user = await get_user_by_username(db, credentials.username)
    if not user or not verify_password(credentials.password, user.hashed_password):
        logger.warning("Failed login attempt for username: %s", credentials.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Generate session API key
    plaintext_key = generate_api_key()
    hashed_key = hash_api_key(plaintext_key)

    await create_api_key(
        db,
        user_id=user.id,
        hashed_key=hashed_key,
        name=f"Session key (login)",
        expires_in_days=30
    )

    logger.info("User %s logged in successfully", user.username)

    return LoginResponse(
        api_key=plaintext_key,
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at
        ),
        message="Login successful. Use the api_key in X-API-Key header for authenticated requests."
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user account.
    """
    # Check if username exists
    existing_user = await get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email exists
    existing_email = await get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    hashed_pwd = hash_password(user_data.password)
    user = await create_user(db, user_data, hashed_pwd)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at
    )


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_new_api_key(
    key_data: APIKeyCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new API key for the authenticated user.
    Returns the plaintext API key - save it securely, it won't be shown again!
    """
    # Generate API key
    plaintext_key = generate_api_key()
    hashed_key = hash_api_key(plaintext_key)

    # Store in database
    db_api_key = await create_api_key(
        db,
        user_id=user.id,
        hashed_key=hashed_key,
        name=key_data.name,
        expires_in_days=key_data.expires_in_days
    )

    logger.info("Created API key '%s' for user %s", key_data.name, user.username)

    return APIKeyResponse(
        id=db_api_key.id,
        name=db_api_key.name,
        key=plaintext_key,  # Only shown once!
        is_active=db_api_key.is_active,
        created_at=db_api_key.created_at,
        expires_at=db_api_key.expires_at
    )


@router.get("/api-keys", response_model=List[dict])
async def list_api_keys(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all API keys for the authenticated user.
    Does not return the actual key values.
    """
    keys = await get_user_api_keys(db, user.id)

    return [
        {
            "id": k.id,
            "name": k.name,
            "is_active": k.is_active,
            "created_at": k.created_at,
            "last_used_at": k.last_used_at,
            "expires_at": k.expires_at
        }
        for k in keys
    ]


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke (deactivate) an API key.
    """
    await revoke_api_key(db, key_id, user.id)
    logger.info("Revoked API key %d for user %s", key_id, user.username)
    return None


@router.get("/rate-limits")
async def get_rate_limits(user: User = Depends(get_current_user)):
    """
    Get current rate limit usage for the authenticated user.
    """
    minute_used, minute_limit, hour_used, hour_limit = rate_limiter.get_limits(user.id)

    return {
        "minute": {
            "used": minute_used,
            "limit": minute_limit,
            "remaining": max(0, minute_limit - minute_used)
        },
        "hour": {
            "used": hour_used,
            "limit": hour_limit,
            "remaining": max(0, hour_limit - hour_used)
        }
    }
