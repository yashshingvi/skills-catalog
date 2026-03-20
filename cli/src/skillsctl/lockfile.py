"""Manages the skills.yaml lockfile."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml


DEFAULT_SOURCE = "http://localhost:8000"
LOCKFILE_NAME = "skills.yaml"


class InstalledItem:
    """Metadata for a single installed item."""

    def __init__(self, version: str, path: Optional[str] = None) -> None:
        self.version = version
        self.path = path  # custom install dir, relative to project root; None = default


class Lockfile:
    def __init__(self, path: Path, source: str, installed: dict[str, InstalledItem]) -> None:
        self.path = path
        self.source = source
        self.installed = installed  # name -> InstalledItem

    @classmethod
    def find(cls, start: Path | None = None) -> "Lockfile":
        """Walk up from start (default: cwd) looking for skills.yaml."""
        cwd = start or Path.cwd()
        current = cwd
        while True:
            candidate = current / LOCKFILE_NAME
            if candidate.exists():
                return cls.load(candidate)
            parent = current.parent
            if parent == current:
                break
            current = parent
        # Not found — return a default at cwd
        return cls(path=cwd / LOCKFILE_NAME, source=DEFAULT_SOURCE, installed={})

    @classmethod
    def load(cls, path: Path) -> "Lockfile":
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text) or {}
        installed: dict[str, InstalledItem] = {}
        for name, value in (data.get("installed") or {}).items():
            if isinstance(value, str):
                # backward-compat: old format stored version as a bare string
                installed[name] = InstalledItem(version=value)
            else:
                installed[name] = InstalledItem(
                    version=str(value.get("version", "1.0.0")),
                    path=value.get("path"),
                )
        return cls(path=path, source=data.get("source", DEFAULT_SOURCE), installed=installed)

    def save(self) -> None:
        serialized: dict = {}
        for name, item in sorted(self.installed.items()):
            if item.path is None:
                serialized[name] = item.version
            else:
                serialized[name] = {"version": item.version, "path": item.path}
        data = {
            "source": self.source,
            "installed": serialized,
        }
        self.path.write_text(
            yaml.dump(data, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

    def add(self, name: str, version: str, path: Optional[str] = None) -> None:
        self.installed[name] = InstalledItem(version=version, path=path)

    def remove(self, name: str) -> bool:
        return self.installed.pop(name, None) is not None

    def has(self, name: str) -> bool:
        return name in self.installed

    def get_version(self, name: str) -> Optional[str]:
        item = self.installed.get(name)
        return item.version if item else None

    def get_path(self, name: str) -> Optional[str]:
        item = self.installed.get(name)
        return item.path if item else None
