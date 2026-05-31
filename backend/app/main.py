"""
BorderVision v2.0 — FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: initialize database tables
    await init_db()
    yield
    # Shutdown: cleanup resources if needed


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered single-camera video analytics for pedestrian boundary monitoring.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS Middleware ───────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health Check ──────────────────────────────────────────────
@app.get("/api/v2/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# ─── Route Registration ────────────────────────────────────────
from app.api import auth, cameras, events, persons, stream, export

app.include_router(auth.router)
app.include_router(cameras.router)
app.include_router(events.router)
app.include_router(persons.router)
app.include_router(stream.router)
app.include_router(export.router)
