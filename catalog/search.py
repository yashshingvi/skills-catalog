"""In-memory search and filter over the catalog store."""
from __future__ import annotations

import math

from .models import CatalogItem, SearchResult, TagCount
from . import store


def _matches_text(item: CatalogItem, q: str) -> tuple[bool, str]:
    """Return (matched, snippet). Searches name, description, tags, raw_content."""
    ql = q.lower()
    snippet = ""

    for field in (item.name, item.description, " ".join(item.tags)):
        if ql in field.lower():
            snippet = snippet or field[:200]
            return True, snippet

    # Search raw content, return surrounding context as snippet
    content_lower = item.raw_content.lower()
    idx = content_lower.find(ql)
    if idx != -1:
        start = max(0, idx - 60)
        end = min(len(item.raw_content), idx + 140)
        snippet = ("…" if start else "") + item.raw_content[start:end].strip() + "…"
        return True, snippet

    return False, ""


def list_items(
    *,
    category: str | None = None,
    tags: list[str] | None = None,
    author: str | None = None,
    include_deprecated: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    items = store.all_items()

    if not include_deprecated:
        items = [i for i in items if not i.deprecated]
    if category:
        items = [i for i in items if i.category == category]
    if author:
        items = [i for i in items if i.author == author]
    if tags:
        tag_set = set(tags)
        items = [i for i in items if tag_set.issubset(set(i.tags))]

    items.sort(key=lambda i: i.name.lower())
    total = len(items)
    offset = (page - 1) * page_size
    page_items = items[offset: offset + page_size]

    return {
        "items": page_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, math.ceil(total / page_size)),
    }


def search_items(
    query: str,
    *,
    category: str | None = None,
    tags: list[str] | None = None,
    author: str | None = None,
    include_deprecated: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    items = store.all_items()

    if not include_deprecated:
        items = [i for i in items if not i.deprecated]
    if category:
        items = [i for i in items if i.category == category]
    if author:
        items = [i for i in items if i.author == author]
    if tags:
        tag_set = set(tags)
        items = [i for i in items if tag_set.issubset(set(i.tags))]

    results: list[SearchResult] = []
    for item in items:
        matched, snippet = _matches_text(item, query)
        if matched:
            results.append(SearchResult(item=item, snippet=snippet))

    results.sort(key=lambda r: r.item.name.lower())
    total = len(results)
    offset = (page - 1) * page_size

    return {
        "results": results[offset: offset + page_size],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, math.ceil(total / page_size)),
        "query": query,
    }


def get_latest_by_name(name: str) -> CatalogItem | None:
    versions = store.get_by_name(name)
    if not versions:
        return None
    try:
        from packaging.version import Version, InvalidVersion
        def key(i: CatalogItem):
            try:
                return Version(i.version)
            except InvalidVersion:
                return Version("0.0.0")
        return max(versions, key=key)
    except ImportError:
        return max(versions, key=lambda i: i.version)


def get_all_versions(name: str) -> list[CatalogItem]:
    versions = store.get_by_name(name)
    try:
        from packaging.version import Version, InvalidVersion
        def key(i: CatalogItem):
            try:
                return Version(i.version)
            except InvalidVersion:
                return Version("0.0.0")
        return sorted(versions, key=key, reverse=True)
    except ImportError:
        return sorted(versions, key=lambda i: i.version, reverse=True)


def get_tags(category: str | None = None) -> list[TagCount]:
    items = store.all_items()
    items = [i for i in items if not i.deprecated]
    if category:
        items = [i for i in items if i.category == category]

    counts: dict[str, int] = {}
    for item in items:
        for tag in item.tags:
            counts[tag] = counts.get(tag, 0) + 1

    return [
        TagCount(tag=t, count=c)
        for t, c in sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    ]
