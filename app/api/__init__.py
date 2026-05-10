"""
API routers for Grammar-LLM-Bridge.
"""
from app.api.v2 import router as v2_router
from app.api.auth import router as auth_router

__all__ = ["auth_router", "v2_router"]
