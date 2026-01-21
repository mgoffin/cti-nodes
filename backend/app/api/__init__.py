"""API route modules."""

from fastapi import APIRouter

from . import nodes, tags, edges, search, extracted, auth, users, audit, comments, export

router = APIRouter()

router.include_router(nodes.router, prefix="/nodes", tags=["nodes"])
router.include_router(tags.router, prefix="/tags", tags=["tags"])
router.include_router(edges.router, prefix="/edges", tags=["edges"])
router.include_router(search.router, prefix="/search", tags=["search"])
router.include_router(extracted.router, prefix="/extracted", tags=["extracted"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(audit.router, prefix="/audit", tags=["audit"])
router.include_router(comments.router, tags=["comments"])
router.include_router(export.router)
