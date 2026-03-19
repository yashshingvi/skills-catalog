"""
Settings — all values are overridable via environment variables prefixed CATALOG_.

Examples:
  CATALOG_CONTENT_DIR=/repos/my-enterprise-playbooks/productivity
  CATALOG_CONTENT_REPO=https://github.com/org/playbooks.git
  CATALOG_CONTENT_BRANCH=main
  CATALOG_PORT=9000
"""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Root folder to scan recursively for .md files.
    content_dir: Path = Path("content")

    # Git content source (optional — overrides content_dir when set)
    content_repo: str = ""                           # git URL
    content_branch: str = "main"                     # branch to track
    content_cache_dir: Path = Path(".content-cache") # local clone path
    sync_interval: int = 300                         # seconds between pulls, 0=disable

    # Webhook secret for POST /api/v1/webhook/refresh
    webhook_secret: str = ""

    host: str = "0.0.0.0"
    port: int = 8000
    watcher_debounce: float = 0.5

    model_config = {"env_prefix": "CATALOG_"}


settings = Settings()
