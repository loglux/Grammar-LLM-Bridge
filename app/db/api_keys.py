"""
API key database operations.
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.connection import Base
from app.models.auth import APIKey as APIKeyModel


class APIKeyTable(Base):
    """SQLAlchemy APIKey table."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    key = Column(String, unique=True, index=True, nullable=False)  # hashed
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)


async def create_api_key(
    db: AsyncSession,
    user_id: int,
    hashed_key: str,
    name: str,
    expires_in_days: int | None = None
) -> APIKeyModel:
    """Create a new API key."""
    expires_at = None
    if expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

    db_key = APIKeyTable(
        user_id=user_id,
        key=hashed_key,
        name=name,
        expires_at=expires_at
    )
    db.add(db_key)
    await db.flush()
    await db.refresh(db_key)
    return APIKeyModel(
        id=db_key.id,
        user_id=db_key.user_id,
        key=db_key.key,
        name=db_key.name,
        is_active=db_key.is_active,
        created_at=db_key.created_at,
        last_used_at=db_key.last_used_at,
        expires_at=db_key.expires_at
    )


async def get_api_key_by_key(db: AsyncSession, hashed_key: str) -> APIKeyModel | None:
    """Get API key by key value (hashed)."""
    result = await db.execute(
        select(APIKeyTable).where(APIKeyTable.key == hashed_key)
    )
    db_key = result.scalar_one_or_none()
    if not db_key:
        return None
    return APIKeyModel(
        id=db_key.id,
        user_id=db_key.user_id,
        key=db_key.key,
        name=db_key.name,
        is_active=db_key.is_active,
        created_at=db_key.created_at,
        last_used_at=db_key.last_used_at,
        expires_at=db_key.expires_at
    )


async def get_user_api_keys(db: AsyncSession, user_id: int) -> list[APIKeyModel]:
    """Get all API keys for a user."""
    result = await db.execute(
        select(APIKeyTable).where(APIKeyTable.user_id == user_id)
    )
    db_keys = result.scalars().all()
    return [
        APIKeyModel(
            id=k.id,
            user_id=k.user_id,
            key=k.key,
            name=k.name,
            is_active=k.is_active,
            created_at=k.created_at,
            last_used_at=k.last_used_at,
            expires_at=k.expires_at
        )
        for k in db_keys
    ]


async def update_api_key_last_used(db: AsyncSession, api_key_id: int):
    """Update last_used_at timestamp for an API key."""
    result = await db.execute(
        select(APIKeyTable).where(APIKeyTable.id == api_key_id)
    )
    db_key = result.scalar_one_or_none()
    if db_key:
        db_key.last_used_at = datetime.utcnow()
        await db.flush()


async def revoke_api_key(db: AsyncSession, api_key_id: int, user_id: int):
    """Revoke (deactivate) an API key."""
    result = await db.execute(
        select(APIKeyTable).where(
            APIKeyTable.id == api_key_id,
            APIKeyTable.user_id == user_id
        )
    )
    db_key = result.scalar_one_or_none()
    if db_key:
        db_key.is_active = False
        await db.flush()
