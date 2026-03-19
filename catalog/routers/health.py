from fastapi import APIRouter, Request
from ..config import settings
from ..models import HealthResponse
from .. import store

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    watcher = request.app.state.watcher

    sha = ""
    if settings.content_repo:
        try:
            from ..git_source import get_head_sha
            sha = get_head_sha(settings.content_cache_dir.resolve())
        except Exception:
            pass

    return HealthResponse(
        status="ok",
        item_count=store.count(),
        watcher_alive=watcher.is_alive,
        content_dir=str(request.app.state.content_dir),
        content_repo=settings.content_repo,
        content_branch=settings.content_branch if settings.content_repo else "",
        last_sync_sha=sha,
    )
