"""
Production-ready FastAPI application with:
- Proper lifecycle management
- Rate limiting
- Connection pooling
- Health checks
- Prometheus metrics (optional)
"""
import logging
from contextlib import asynccontextmanager
from typing import Dict
import time

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import httpx

import os
from ai_companion.interfaces.whatsapp.whatsapp_response import whatsapp_router

logger = logging.getLogger(__name__)

# Rate limiter configuration
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting WhatsApp Webhook Service...")

    try:
        # Create httpx client pool for WhatsApp API calls
        app.state.httpx_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=100, max_connections=200),
        )
        logger.info("HTTP client pool created")

        # Verify required environment variables
        if not os.getenv("WHATSAPP_TOKEN"):
            logger.warning("WHATSAPP_TOKEN environment variable is not set")
        if not os.getenv("WHATSAPP_PHONE_NUMBER_ID"):
            logger.warning("WHATSAPP_PHONE_NUMBER_ID environment variable is not set")

        logger.info("✅ Application startup complete")

        yield

    finally:
        # Shutdown
        logger.info("Shutting down WhatsApp Webhook Service...")

        # Close HTTP client
        if hasattr(app.state, 'httpx_client'):
            await app.state.httpx_client.aclose()
            logger.info("HTTP client closed")

        logger.info("✅ Application shutdown complete")


# Create FastAPI app with lifecycle
app = FastAPI(
    title="WhatsApp Multi-Business Webhook",
    description="Production-ready webhook handler for multiple WhatsApp Business accounts",
    version="2.0.0",
    lifespan=lifespan,
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include WhatsApp router
app.include_router(whatsapp_router)


# Health check endpoint
@app.get("/health", tags=["Health"])
@limiter.limit("100/minute")
async def health_check(request: Request) -> Dict:
    """
    Health check endpoint for load balancers and monitoring.
    """
    try:
        # Check if required environment variables are set
        has_token = bool(os.getenv("WHATSAPP_TOKEN"))
        has_phone_id = bool(os.getenv("WHATSAPP_PHONE_NUMBER_ID"))

        status_val = "healthy" if (has_token and has_phone_id) else "degraded"

        return {
            "status": status_val,
            "timestamp": time.time(),
            "config": {
                "whatsapp_token_configured": has_token,
                "whatsapp_phone_number_id_configured": has_phone_id,
            },
            "service": "whatsapp-webhook",
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time(),
            }
        )


# Readiness check (for Kubernetes)
@app.get("/ready", tags=["Health"])
@limiter.limit("100/minute")
async def readiness_check(request: Request) -> Dict:
    """
    Readiness check for orchestration platforms.
    Ensures service is ready to handle traffic.
    """
    try:
        # Check if required environment variables are set
        has_token = bool(os.getenv("WHATSAPP_TOKEN"))
        has_phone_id = bool(os.getenv("WHATSAPP_PHONE_NUMBER_ID"))

        if not (has_token and has_phone_id):
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"ready": False, "reason": "Required environment variables not configured"}
            )

        return {"ready": True, "timestamp": time.time()}

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"ready": False, "error": str(e), "timestamp": time.time()}
        )


# Metrics endpoint (basic)
@app.get("/metrics", tags=["Monitoring"])
@limiter.limit("10/minute")
async def metrics(request: Request) -> Dict:
    """
    Basic metrics endpoint. For production, consider Prometheus integration.
    """
    try:
        return {
            "config": {
                "whatsapp_token_configured": bool(os.getenv("WHATSAPP_TOKEN")),
                "whatsapp_phone_number_id_configured": bool(os.getenv("WHATSAPP_PHONE_NUMBER_ID")),
            },
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        return {"error": str(e), "timestamp": time.time()}


# Cache management endpoints removed - no longer using database cache


# Middleware for request timing and logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing information"""
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.3f}s"
    )

    # Add custom headers
    response.headers["X-Process-Time"] = str(duration)

    return response
