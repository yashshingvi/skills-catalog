"""Manages the skills.yaml lockfile."""
from __future__ import annotations

from pathlib import Path

import yaml


DEFAULT_SOURCE = "http://localhost:8000"
LOCKFILE_NAME = "skills.yaml"


class Lockfile:
    def __init__(self, path: Path, source: str, installed: dict[str, str]) -> None:
        self.path = path
        self.source = source
        self.installed = installed  # name -> version

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
        return cls(
            path=path,
            source=data.get("source", DEFAULT_SOURCE),
            installed=data.get("installed", {}),
        )

    def save(self) -> None:
        data = {
            "source": self.source,
            "installed": dict(sorted(self.installed.items())),
        }
        self.path.write_text(
            yaml.dump(data, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

    def add(self, name: str, version: str) -> None:
        self.installed[name] = version

    def remove(self, name: str) -> bool:
        return self.installed.pop(name, None) is not None

    def has(self, name: str) -> bool:
        return name in self.installed
