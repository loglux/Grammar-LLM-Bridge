"""
FastAPI application and endpoints.
Entry point for the Grammar-LLM-Bridge server.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.config import LLM_MODEL
from app.models import CheckRequest
from app.api import v2_router, auth_router

# Initialize FastAPI app
app = FastAPI(title="Grammar-LLM-Bridge", version="2.0-json-schema")

# CORS middleware - allows browser requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key authentication middleware (optional, backward compatible)
# Validates X-API-Key header and sets request.state.user
from app.auth.middleware import api_key_auth_middleware
app.middleware("http")(api_key_auth_middleware)

# Include routers
app.include_router(v2_router)
app.include_router(auth_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    from app.db import init_db
    await init_db()
    logger.info("Database initialized")


logger = logging.getLogger("customlt")
logging.basicConfig(level=logging.DEBUG)

# Log configuration on startup
logger.info("=" * 60)
logger.info("Grammar-LLM-Bridge v2.0 - JSON Schema Edition")
logger.info(f"  Model: {LLM_MODEL}")
logger.info("=" * 60)


# Custom OpenAPI schema
def custom_openapi():
    """
    Override OpenAPI schema to document that /v2/check accepts both
    application/json and application/x-www-form-urlencoded.
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Grammar LLM Bridge",
        version="1.0.0",
        description="LanguageTool-compatible API with LLM backend",
        routes=app.routes,
    )

    # Add support for both Content-Types in /v2/check documentation
    if "/v2/check" in openapi_schema.get("paths", {}):
        post_op = openapi_schema["paths"]["/v2/check"].get("post")
        if post_op:
            # Generate schema from CheckRequest model
            check_request_schema = CheckRequest.model_json_schema()

            post_op["requestBody"] = {
                "required": False,
                "content": {
                    "application/json": {
                        "schema": check_request_schema
                    },
                    "application/x-www-form-urlencoded": {
                        "schema": check_request_schema
                    }
                }
            }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
