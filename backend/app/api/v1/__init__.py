from app.api.v1.auth import router as auth_router
from app.api.v1.classes import router as classes_router
from app.api.v1.papers import router as papers_router
from app.api.v1.submissions import router as submissions_router

__all__ = ["auth_router", "classes_router", "papers_router", "submissions_router"]
