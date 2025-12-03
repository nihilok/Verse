import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes import router
from app.core.config import get_settings
from app.core.database import Base, engine
from app.core.middleware import AnonymousUserMiddleware
from app.core.rate_limiter import limiter
from app.core.security_headers import SecurityHeadersMiddleware

# Configure logging for the application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Output to console (captured by Docker/systemd in production)
    ],
)

# Set specific log levels for noisy libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("anthropic").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup: Initialize database tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: cleanup if needed


# Initialize FastAPI app
settings = get_settings()
app = FastAPI(
    title="Verse API",
    description="Interactive Bible reader with AI-powered insights",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Accept", "Cookie", "Authorization"],
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add anonymous user middleware
app.add_middleware(AnonymousUserMiddleware)

# Include routers
app.include_router(router, prefix="/api", tags=["bible"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Verse API - Interactive Bible Reader with AI Insights",
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
