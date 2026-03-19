from fastapi import APIRouter, Request
from ..models import HealthResponse
from .. import store

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    watcher = request.app.state.watcher
    return HealthResponse(
        status="ok",
        item_count=store.count(),
        watcher_alive=watcher.is_alive,
        content_dir=str(request.app.state.content_dir),
    )
