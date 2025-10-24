from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.database import engine, Base
from app.api.routes import router

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
settings = get_settings()
app = FastAPI(
    title="Verse API",
    description="Interactive Bible reader with AI-powered insights",
    version="1.0.0",
    debug=settings.debug
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api", tags=["bible"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Verse API - Interactive Bible Reader with AI Insights",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
