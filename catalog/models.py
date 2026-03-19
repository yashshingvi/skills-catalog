from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field, field_validator


class CatalogItem(BaseModel):
    file_path: str           # relative to cwd, stable key
    name: str
    description: str
    version: str = "1.0.0"
    category: str = "skills"
    tags: list[str] = Field(default_factory=list)
    author: str = ""
    deprecated: bool = False
    requires: list[str] = Field(default_factory=list)
    changelog: str = ""
    raw_content: str = ""    # markdown body (no frontmatter)
    file_mtime: float = 0.0

    model_config = {"extra": "ignore"}

    @field_validator("tags", "requires", mode="before")
    @classmethod
    def coerce_list(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [v]
        return list(v) if v else []

    @field_validator("deprecated", mode="before")
    @classmethod
    def coerce_bool(cls, v: Any) -> bool:
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes")
        return bool(v)


class SearchResult(BaseModel):
    item: CatalogItem
    snippet: str = ""


class TagCount(BaseModel):
    tag: str
    count: int


class HealthResponse(BaseModel):
    status: str
    item_count: int
    watcher_alive: bool
    content_dir: str
