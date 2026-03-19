import logging
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

from .config import settings
from .indexer import index_file, remove_file

logger = logging.getLogger(__name__)

_lock = threading.Lock()  # serialise concurrent FS events


class CatalogEventHandler(FileSystemEventHandler):
    def _handle_upsert(self, path: str) -> None:
        p = Path(path)
        if p.suffix.lower() != ".md" or not p.exists():
            return
        time.sleep(settings.watcher_debounce)
        with _lock:
            index_file(p)

    def _handle_delete(self, path: str) -> None:
        if not path.endswith(".md"):
            return
        with _lock:
            remove_file(Path(path))

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._handle_upsert(event.src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._handle_upsert(event.src_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._handle_delete(event.src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._handle_delete(event.src_path)
            self._handle_upsert(event.dest_path)


class CatalogWatcher:
    def __init__(self) -> None:
        self._observer: Observer | None = None

    def start(self) -> None:
        content_dir = settings.content_dir.resolve()
        content_dir.mkdir(parents=True, exist_ok=True)
        self._observer = Observer()
        self._observer.schedule(CatalogEventHandler(), str(content_dir), recursive=True)
        self._observer.start()
        logger.info("Watcher started on %s", content_dir)

    def stop(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join()
            logger.info("Watcher stopped")

    @property
    def is_alive(self) -> bool:
        return self._observer is not None and self._observer.is_alive()
