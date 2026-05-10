"""
FastAPI dependencies for authentication.
"""
from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from app.models.auth import User


async def get_optional_user(request: Request) -> Optional[User]:
    """
    Get current user from request state if authenticated.
    Returns None if not authenticated (does not raise exception).

    Usage:
        async def endpoint(user: Optional[User] = Depends(get_optional_user)):
            if user:
                # authenticated request
            else:
                # anonymous request
    """
    return getattr(request.state, "user", None)


async def get_current_user(user: Optional[User] = Depends(get_optional_user)) -> User:
    """
    Get current authenticated user.
    Raises 401 if not authenticated.

    Usage:
        async def endpoint(user: User = Depends(get_current_user)):
            # user is guaranteed to be authenticated
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """
    Require admin privileges.
    Raises 403 if user is not admin.

    Usage:
        async def endpoint(user: User = Depends(require_admin)):
            # user is guaranteed to be admin
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user
