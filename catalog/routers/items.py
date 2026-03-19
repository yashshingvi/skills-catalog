from fastapi import APIRouter, HTTPException, Query
from ..models import CatalogItem, SearchResult
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
