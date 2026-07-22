"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import health, data, report, clawby_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # Print config summary on startup
    print(f"🔧  Clawby Report Generator — backend starting")
    print(f"    Port:         {settings.backend_port}")
    print(f"    Clawby key:   {'✅ configured' if settings.clawby_api_key else '❌ missing'}")
    print(f"    LLM key:      {'✅ configured' if settings.llm_api_key else '❌ missing'}")
    print(f"    LLM provider: {settings.llm_provider_type} ({settings.llm_api_base})")
    print(f"    Data dir:     {settings.data_dir}")
    print()
    yield


app = FastAPI(
    title="Clawby Stock Report Generator",
    description="Generate professional US equity analysis reports powered by Clawby data & LLM.",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS — allow the frontend dev server and Docker network
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(data.router)
app.include_router(report.router)
app.include_router(clawby_config.router)
