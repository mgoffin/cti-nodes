"""API route modules."""

from fastapi import APIRouter

from . import nodes, tags, edges, search, extracted

router = APIRouter()

router.include_router(nodes.router, prefix="/nodes", tags=["nodes"])
router.include_router(tags.router, prefix="/tags", tags=["tags"])
router.include_router(edges.router, prefix="/edges", tags=["edges"])
router.include_router(search.router, prefix="/search", tags=["search"])
router.include_router(extracted.router, prefix="/extracted", tags=["extracted"])
