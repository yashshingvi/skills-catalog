from fastapi import APIRouter, Query
from ..models import TagCount
from ..search import get_tags

router = APIRouter(prefix="/api/v1")


@router.get("/tags", response_model=list[TagCount])
def tags(category: str | None = Query(None)) -> list[TagCount]:
    return get_tags(category=category)
