"""FastAPI application entrypoint."""

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .api import router as api_router
from .core.config import settings
from .core.database import init_database, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await init_database()
    await load_reference_data()
    yield
    # Shutdown (nothing to do)


async def load_reference_data():
    """Load threat actor aliases into the database."""
    data_path = Path(__file__).parent / "data" / "threat_actors.json"
    if not data_path.exists():
        return

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    async with get_db() as db:
        for actor in data.get("actors", []):
            canonical = actor["canonical_name"]
            for alias in actor.get("aliases", []):
                await db.execute(
                    """
                    INSERT OR REPLACE INTO threat_actor_aliases (alias, canonical_name)
                    VALUES (?, ?)
                    """,
                    (alias.lower(), canonical),
                )
            # Also map canonical name to itself
            await db.execute(
                """
                INSERT OR REPLACE INTO threat_actor_aliases (alias, canonical_name)
                VALUES (?, ?)
                """,
                (canonical.lower(), canonical),
            )
        await db.commit()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A lightweight graph-based intelligence notebook for threat intel",
    lifespan=lifespan,
)

# CORS middleware for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.app_version}


# API routes
app.include_router(api_router, prefix="/api")

# Serve frontend static files in production
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    # Mount static assets (JS, CSS, images) under /assets
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # Serve other static files like favicon
    @app.get("/favicon.svg")
    async def favicon():
        favicon_path = frontend_dist / "favicon.svg"
        if favicon_path.exists():
            return FileResponse(favicon_path, media_type="image/svg+xml")
        return {"error": "not found"}

    # Serve index.html for root
    @app.get("/")
    async def serve_root():
        index_path = frontend_dist / "index.html"
        if index_path.exists():
            return FileResponse(index_path, media_type="text/html")
        return {"error": "not found"}

    # SPA routes - explicitly define frontend routes to avoid catching API routes
    @app.get("/node/{node_id:path}")
    async def serve_spa_node(node_id: str):
        index_path = frontend_dist / "index.html"
        if index_path.exists():
            return FileResponse(index_path, media_type="text/html")
        return {"error": "not found"}

    @app.get("/new")
    async def serve_spa_new():
        index_path = frontend_dist / "index.html"
        if index_path.exists():
            return FileResponse(index_path, media_type="text/html")
        return {"error": "not found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
