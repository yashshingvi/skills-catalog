from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from ..models import BundleItem, BundleResponse, CatalogItem, SearchResult
from .. import search, store
from ..indexer import scan_and_index

router = APIRouter(prefix="/api/v1")


@router.get("/items", response_model=dict)
def list_items(
    category: str | None = Query(None),
    tags: list[str] | None = Query(None),
    author: str | None = Query(None),
    deprecated: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return search.list_items(
        category=category,
        tags=tags,
        author=author,
        include_deprecated=deprecated,
        page=page,
        page_size=page_size,
    )


@router.get("/items/search", response_model=dict)
def search_items(
    q: str = Query(..., min_length=1),
    category: str | None = Query(None),
    tags: list[str] | None = Query(None),
    author: str | None = Query(None),
    deprecated: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return search.search_items(
        q,
        category=category,
        tags=tags,
        author=author,
        include_deprecated=deprecated,
        page=page,
        page_size=page_size,
    )


@router.get("/items/by-path", response_model=CatalogItem)
def by_path(path: str = Query(...)):
    item = store.get_by_path(path)
    if not item:
        raise HTTPException(404, f"No item at path: {path}")
    return item


@router.post("/items/refresh")
def refresh():
    count = scan_and_index()
    return {"refreshed": count, "total": store.count()}


@router.get("/items/bundle", response_model=BundleResponse)
def bundle(items: str = Query(..., description="Comma-separated item names")):
    names = [n.strip() for n in items.split(",") if n.strip()]
    result_items: list[BundleItem] = []
    errors: list[str] = []

    for name in names:
        item = search.get_latest_by_name(name)
        if not item:
            errors.append(name)
            continue
        file_path = Path(item.file_path)
        if not file_path.exists():
            file_path = Path.cwd() / item.file_path
        if not file_path.exists():
            errors.append(name)
            continue
        content = file_path.read_text(encoding="utf-8")
        result_items.append(BundleItem(
            name=item.name,
            version=item.version,
            category=item.category,
            content=content,
        ))

    return BundleResponse(items=result_items, errors=errors)


@router.get("/items/{name}/raw")
def get_raw(name: str):
    item = search.get_latest_by_name(name)
    if not item:
        raise HTTPException(404, f"No item named: {name}")
    file_path = Path(item.file_path)
    if not file_path.exists():
        file_path = Path.cwd() / item.file_path
    if not file_path.exists():
        raise HTTPException(404, f"Source file not found: {item.file_path}")
    content = file_path.read_text(encoding="utf-8")
    return PlainTextResponse(content, media_type="text/markdown")


@router.get("/items/{name}/versions", response_model=list[CatalogItem])
def versions(name: str):
    items = search.get_all_versions(name)
    if not items:
        raise HTTPException(404, f"No item named: {name}")
    return items


@router.get("/items/{name}", response_model=CatalogItem)
def get_item(name: str):
    item = search.get_latest_by_name(name)
    if not item:
        raise HTTPException(404, f"No item named: {name}")
    return item
