"""
User database operations.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.connection import Base
from app.models.auth import User as UserModel, UserCreate


class UserTable(Base):
    """SQLAlchemy User table."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


async def create_user(db: AsyncSession, user: UserCreate, hashed_password: str) -> UserModel:
    """Create a new user."""
    db_user = UserTable(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    await db.flush()
    await db.refresh(db_user)
    return UserModel(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        hashed_password=db_user.hashed_password,
        is_active=db_user.is_active,
        is_admin=db_user.is_admin,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[UserModel]:
    """Get user by ID."""
    result = await db.execute(select(UserTable).where(UserTable.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        return None
    return UserModel(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        hashed_password=db_user.hashed_password,
        is_active=db_user.is_active,
        is_admin=db_user.is_admin,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[UserModel]:
    """Get user by username."""
    result = await db.execute(select(UserTable).where(UserTable.username == username))
    db_user = result.scalar_one_or_none()
    if not db_user:
        return None
    return UserModel(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        hashed_password=db_user.hashed_password,
        is_active=db_user.is_active,
        is_admin=db_user.is_admin,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserModel]:
    """Get user by email."""
    result = await db.execute(select(UserTable).where(UserTable.email == email))
    db_user = result.scalar_one_or_none()
    if not db_user:
        return None
    return UserModel(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        hashed_password=db_user.hashed_password,
        is_active=db_user.is_active,
        is_admin=db_user.is_admin,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at
    )
