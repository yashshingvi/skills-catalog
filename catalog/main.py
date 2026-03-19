import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import markdown as md_lib
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings
from .indexer import scan_and_index
from .watcher import CatalogWatcher
from . import store, search
from .routers import health, tags, items

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_watcher = CatalogWatcher()


async def _periodic_sync(interval: int) -> None:
    """Background task: pull latest git changes and re-index."""
    from .git_source import pull_latest
    while True:
        await asyncio.sleep(interval)
        try:
            changed = pull_latest(
                settings.content_cache_dir.resolve(),
                settings.content_branch,
            )
            if changed:
                scan_and_index()
        except Exception as exc:
            logger.error("Periodic sync failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # If a git repo is configured, clone it and override content_dir
    if settings.content_repo:
        from .git_source import ensure_repo
        cache_path = ensure_repo(
            settings.content_repo,
            settings.content_branch,
            settings.content_cache_dir.resolve(),
        )
        settings.content_dir = cache_path
        logger.info("Content source: git repo %s → %s", settings.content_repo, cache_path)

    app.state.watcher = _watcher
    app.state.content_dir = settings.content_dir.resolve()

    scan_and_index()
    _watcher.start()

    # Start periodic git sync if configured
    sync_task = None
    if settings.content_repo and settings.sync_interval > 0:
        sync_task = asyncio.create_task(_periodic_sync(settings.sync_interval))
        logger.info("Periodic sync enabled: every %ds", settings.sync_interval)

    yield

    if sync_task:
        sync_task.cancel()
    _watcher.stop()


app = FastAPI(title="Skills Catalog", version="1.0.0", lifespan=lifespan)

# ── Static files & templates ───────────────────────────────────────────────────
_here = Path(__file__).parent.parent
app.mount("/static", StaticFiles(directory=str(_here / "static")), name="static")
templates = Jinja2Templates(directory=str(_here / "templates"))


# ── API routers ────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(tags.router)
app.include_router(items.router)

# Webhook router (optional git refresh endpoint)
from .routers import webhook
app.include_router(webhook.router)


# ── Browser UI ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def ui_index(
    request: Request,
    q: str = Query(""),
    category: str = Query(""),
    tag: str = Query(""),
):
    tag_list = [tag] if tag else None
    cat = category or None

    if q:
        result = search.search_items(q, category=cat, tags=tag_list)
        items_list = [r.item for r in result["results"]]
        total = result["total"]
    else:
        result = search.list_items(category=cat, tags=tag_list, page_size=200)
        items_list = result["items"]
        total = result["total"]

    all_tags = search.get_tags()
    categories = sorted({i.category for i in store.all_items()})

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "items": items_list,
            "total": total,
            "query": q,
            "selected_category": category,
            "selected_tag": tag,
            "all_tags": all_tags,
            "categories": categories,
        },
    )


@app.get("/ui/items/{name}", response_class=HTMLResponse)
def ui_item(request: Request, name: str):
    from fastapi import HTTPException
    item = search.get_latest_by_name(name)
    if not item:
        raise HTTPException(404, f"Item not found: {name}")

    versions = search.get_all_versions(name)
    rendered_html = md_lib.markdown(
        item.raw_content,
        extensions=["fenced_code", "tables", "toc", "nl2br"],
    )
    base_url = str(request.base_url).rstrip("/")

    return templates.TemplateResponse(
        "item.html",
        {
            "request": request,
            "item": item,
            "versions": versions,
            "rendered_html": rendered_html,
            "base_url": base_url,
            "api_url": f"{base_url}/api/v1/items/{name}",
            "curl_cmd": f'curl "{base_url}/api/v1/items/{name}"',
        },
    )
