"""Shared fixtures for CLI command tests."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch as mock_patch

import pytest
from click.testing import CliRunner

from skillsctl.lockfile import DEFAULT_SOURCE, Lockfile
from skillsctl.main import cli


def make_lockfile(tmp_path: Path, base_dir: str | None = None) -> Lockfile:
    lf_path = tmp_path / "skills.yaml"
    lf = Lockfile(path=lf_path, source=DEFAULT_SOURCE, installed={}, base_dir=base_dir)
    lf.save()
    return lf


def make_client(items: dict[str, dict] | None = None) -> MagicMock:
    """Return a mock CatalogClient pre-loaded with catalog items."""
    items = items or {}
    client = MagicMock()

    def get_item(name):
        return items.get(name)

    def get_raw(name):
        item = items.get(name)
        return f"# {name}\ncontent" if item else None

    def get_bundle(names):
        result = []
        errors = []
        for name in names:
            item = items.get(name)
            if item:
                result.append({
                    "name": name,
                    "version": item["version"],
                    "category": item["category"],
                    "content": f"# {name}\ncontent",
                })
            else:
                errors.append(name)
        return {"items": result, "errors": errors}

    client.get_item.side_effect = get_item
    client.get_raw.side_effect = get_raw
    client.get_bundle.side_effect = get_bundle
    return client


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def catalog_items():
    return {
        "send-email": {"version": "1.0.0", "category": "skills", "requires": []},
        "http-request": {"version": "2.0.0", "category": "skills", "requires": []},
        "my-agent": {"version": "1.0.0", "category": "agents", "requires": ["http-request"]},
        "my-rule": {"version": "1.0.0", "category": "rules", "requires": []},
    }


def invoke(runner: CliRunner, lockfile: Lockfile, client: MagicMock, *args: str):
    """Invoke the CLI with a pre-configured lockfile and mock client.

    Patches Lockfile.find() so the cli group receives our lockfile,
    and patches CatalogClient so API calls go to our mock.
    """
    with mock_patch.object(Lockfile, "find", return_value=lockfile), \
         mock_patch("skillsctl.main.CatalogClient") as MockCC:
        MockCC.return_value = client
        result = runner.invoke(cli, list(args), catch_exceptions=False)
    return result
