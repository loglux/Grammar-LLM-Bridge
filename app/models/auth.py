"""
Authentication models for Grammar-LLM-Bridge.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class User(BaseModel):
    """User account model."""
    id: Optional[int] = None
    username: str
    email: str
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class APIKey(BaseModel):
    """API key model for authentication."""
    id: Optional[int] = None
    user_id: int
    key: str  # hashed API key
    name: str  # user-friendly name for the key
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class UsageRecord(BaseModel):
    """Usage tracking model."""
    id: Optional[int] = None
    user_id: int
    api_key_id: Optional[int] = None
    endpoint: str
    request_tokens: int = 0
    response_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    status_code: int = 200
    created_at: datetime = Field(default_factory=datetime.utcnow)


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
    expires_in_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    """Schema for API key response."""
    id: int
    name: str
    key: str  # only shown once on creation
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
