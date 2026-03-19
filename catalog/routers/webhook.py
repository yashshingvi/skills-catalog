"""Webhook endpoint for git-based content refresh."""
from fastapi import APIRouter, HTTPException, Header

from ..config import settings
from ..indexer import scan_and_index

router = APIRouter(prefix="/api/v1")


@router.post("/webhook/refresh")
def webhook_refresh(
    x_webhook_secret: str = Header("", alias="X-Webhook-Secret"),
):
    """Pull latest git changes and re-index. Wire to your repo's push webhook."""
    # Validate secret if configured
    if settings.webhook_secret and x_webhook_secret != settings.webhook_secret:
        raise HTTPException(403, "Invalid webhook secret")

    if settings.content_repo:
        from ..git_source import pull_latest
        changed = pull_latest(
            settings.content_cache_dir.resolve(),
            settings.content_branch,
        )
        count = scan_and_index() if changed else 0
        return {"pulled": changed, "indexed": count}
    else:
        count = scan_and_index()
        return {"pulled": False, "indexed": count}
