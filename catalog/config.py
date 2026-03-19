"""
Settings — all values are overridable via environment variables prefixed CATALOG_.

Examples:
  CATALOG_CONTENT_DIR=/repos/my-enterprise-playbooks/productivity
  CATALOG_CONTENT_DIR=C:/repos/tools          # Windows absolute path
  CATALOG_PORT=9000
"""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Root folder to scan recursively for .md files.
    # Can be an absolute path to any repo folder.
    content_dir: Path = Path("content")

    host: str = "0.0.0.0"
    port: int = 8000
    watcher_debounce: float = 0.5  # seconds to wait after FS event before re-parsing

    model_config = {"env_prefix": "CATALOG_"}


settings = Settings()
