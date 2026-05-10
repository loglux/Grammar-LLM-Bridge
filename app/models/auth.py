"""
Authentication models for Grammar-LLM-Bridge.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class User(BaseModel):
    """User account model."""
    id: int | None = None
    username: str
    email: str
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class APIKey(BaseModel):
    """API key model for authentication."""
    id: int | None = None
    user_id: int
    key: str  # hashed API key
    name: str  # user-friendly name for the key
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: datetime | None = None
    expires_at: datetime | None = None


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)."""
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime


class APIKeyCreate(BaseModel):
    """Schema for creating a new API key."""
    name: str
    expires_in_days: int | None = None


class APIKeyResponse(BaseModel):
    """Schema for API key response."""
    id: int
    name: str
    key: str  # only shown once on creation
    is_active: bool
    created_at: datetime
    expires_at: datetime | None
