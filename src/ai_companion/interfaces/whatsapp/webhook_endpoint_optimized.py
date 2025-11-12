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

from ai_companion.interfaces.whatsapp.whatsapp_response import whatsapp_router
from ai_companion.services.business_service_optimized import get_optimized_business_service

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
        # Initialize business service and connection pool
        business_service = await get_optimized_business_service()
        logger.info("Business service initialized")

        # Store in app state for access in routes
        app.state.business_service = business_service

        # Optional: Create httpx client pool for WhatsApp API calls
        app.state.httpx_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=100, max_connections=200),
        )
        logger.info("HTTP client pool created")

        logger.info("✅ Application startup complete")

        yield

    finally:
        # Shutdown
        logger.info("Shutting down WhatsApp Webhook Service...")

        # Close business service connections
        if hasattr(app.state, 'business_service'):
            await app.state.business_service.disconnect()
            logger.info("Business service disconnected")

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
        # Check MongoDB connection
        business_service = await get_optimized_business_service()
        if business_service.client:
            await business_service.client.admin.command('ping')
            db_status = "healthy"
        else:
            db_status = "disconnected"

        return {
            "status": "healthy",
            "timestamp": time.time(),
            "database": db_status,
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
        business_service = await get_optimized_business_service()

        # Check if connection pool is initialized
        if not business_service._is_connected:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"ready": False, "reason": "Database not connected"}
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
        business_service = await get_optimized_business_service()

        # Get cache stats
        cache_size = len(business_service.cache._cache)

        return {
            "cache": {
                "size": cache_size,
                "max_size": business_service.cache.max_size,
                "ttl_seconds": business_service.cache.ttl_seconds,
            },
            "connection_pool": {
                "max_pool_size": business_service.max_pool_size,
                "min_pool_size": business_service.min_pool_size,
            },
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        return {"error": str(e), "timestamp": time.time()}


# Cache management endpoints (admin only - add auth in production)
@app.post("/admin/cache/clear", tags=["Admin"])
@limiter.limit("1/minute")
async def clear_cache(request: Request) -> Dict:
    """Clear business cache. Use with caution."""
    try:
        business_service = await get_optimized_business_service()
        await business_service.clear_cache()
        logger.warning("Business cache cleared via admin endpoint")
        return {"status": "success", "message": "Cache cleared"}
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "error": str(e)}
        )


@app.post("/admin/cache/warmup", tags=["Admin"])
@limiter.limit("1/minute")
async def warmup_cache(request: Request) -> Dict:
    """Warm up business cache with active businesses."""
    try:
        business_service = await get_optimized_business_service()
        await business_service.warmup_cache(limit=100)
        logger.info("Business cache warmed up via admin endpoint")
        return {"status": "success", "message": "Cache warmed up"}
    except Exception as e:
        logger.error(f"Failed to warm up cache: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "error": str(e)}
        )


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
