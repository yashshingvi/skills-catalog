"""Parse markdown files and populate the in-memory store."""
from __future__ import annotations

import logging
from pathlib import Path

import frontmatter

from .config import settings
from .models import CatalogItem
from . import store

logger = logging.getLogger(__name__)


def _infer_category(file_path: Path) -> str:
    """
    Infer category from folder structure when not set in frontmatter.

    Walks the path parts looking for known category keywords, or falls back
    to the immediate parent folder name.

    Examples:
      productivity/tools/rules/foo.md  → "rules"
      content/skills/bar.md            → "skills"
      anything/my-folder/baz.md        → "my-folder"
    """
    known = {"skills", "workflows", "rules", "agents", "tools", "policies", "templates", "guides"}
    parts = [p.lower() for p in file_path.parts]
    # Walk from deepest folder upward (exclude filename)
    for part in reversed(parts[:-1]):
        if part in known:
            return part
    # Fall back to immediate parent directory name
    if len(file_path.parts) >= 2:
        return file_path.parts[-2].lower()
    return "skills"


def parse_file(file_path: Path) -> CatalogItem | None:
    """Return a CatalogItem or None if the file is invalid/missing required fields."""
    try:
        post = frontmatter.load(str(file_path))
    except Exception as exc:
        logger.warning("Cannot parse %s: %s", file_path, exc)
        return None

    meta = dict(post.metadata)
    if "name" not in meta or "description" not in meta:
        logger.warning("Skipping %s — missing required frontmatter (name, description)", file_path)
        return None

    # Infer category from folder if not specified in frontmatter
    if "category" not in meta:
        meta["category"] = _infer_category(file_path)

    try:
        rel_path = str(file_path.relative_to(Path.cwd()))
    except ValueError:
        rel_path = str(file_path)

    try:
        item = CatalogItem(
            file_path=rel_path,
            raw_content=post.content,
            file_mtime=file_path.stat().st_mtime,
            **meta,
        )
    except Exception as exc:
        logger.warning("Skipping %s — invalid frontmatter: %s", file_path, exc)
        return None

    return item


def index_file(file_path: Path) -> bool:
    """Parse and upsert a single file. Returns True on success."""
    item = parse_file(file_path)
    if item is None:
        return False
    store.upsert(item)
    logger.info("Indexed: %s  (%s v%s)", item.file_path, item.name, item.version)
    return True


def remove_file(file_path: Path) -> None:
    try:
        rel_path = str(file_path.relative_to(Path.cwd()))
    except ValueError:
        rel_path = str(file_path)
    store.remove(rel_path)
    logger.info("Removed from index: %s", rel_path)


def scan_and_index() -> int:
    """Walk content_dir, index new/changed files, drop stale entries."""
    content_dir = settings.content_dir.resolve()
    if not content_dir.exists():
        logger.warning("content_dir missing: %s", content_dir)
        return 0

    existing = {item.file_path: item.file_mtime for item in store.all_items()}
    disk_paths: set[str] = set()
    indexed = 0

    for md_file in content_dir.rglob("*.md"):
        try:
            rel = str(md_file.relative_to(Path.cwd()))
        except ValueError:
            rel = str(md_file)

        disk_paths.add(rel)
        mtime = md_file.stat().st_mtime

        if rel in existing and abs(existing[rel] - mtime) < 0.01:
            continue  # unchanged — skip re-parse

        if index_file(md_file):
            indexed += 1

    # Purge records for deleted files
    for stale in set(existing) - disk_paths:
        store.remove(stale)
        logger.info("Purged deleted: %s", stale)

    logger.info("Scan complete — %d indexed/updated, %d total", indexed, store.count())
    return indexed
