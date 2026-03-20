"""Tests for lockfile.py — load, save, backward compat, base_dir, InstalledItem."""
from __future__ import annotations

import pytest
import yaml

from skillsctl.lockfile import DEFAULT_BASE_DIR, DEFAULT_SOURCE, InstalledItem, Lockfile


# ---------------------------------------------------------------------------
# InstalledItem
# ---------------------------------------------------------------------------

def test_installed_item_defaults():
    item = InstalledItem(version="1.2.3")
    assert item.version == "1.2.3"
    assert item.path is None


def test_installed_item_with_path():
    item = InstalledItem(version="2.0.0", path=".claude")
    assert item.path == ".claude"


# ---------------------------------------------------------------------------
# Lockfile.load — backward compat (bare string values)
# ---------------------------------------------------------------------------

def test_load_legacy_bare_string(tmp_path):
    """Old skills.yaml used name: "version" — must still load."""
    lf_path = tmp_path / "skills.yaml"
    lf_path.write_text(
        "source: http://localhost:8000\n"
        "installed:\n"
        "  send-email: '1.0.0'\n"
        "  http-request: '2.3.0'\n",
        encoding="utf-8",
    )
    lf = Lockfile.load(lf_path)
    assert lf.installed["send-email"].version == "1.0.0"
    assert lf.installed["send-email"].path is None
    assert lf.installed["http-request"].version == "2.3.0"
    assert lf.base_dir is None


def test_load_new_dict_format(tmp_path):
    """New format with path dict per item."""
    lf_path = tmp_path / "skills.yaml"
    lf_path.write_text(
        "source: http://localhost:8000\n"
        "base_dir: .claude\n"
        "installed:\n"
        "  my-rule:\n"
        "    version: '1.0.0'\n"
        "    path: .claude/commands\n"
        "  http-request: '2.0.0'\n",
        encoding="utf-8",
    )
    lf = Lockfile.load(lf_path)
    assert lf.base_dir == ".claude"
    assert lf.installed["my-rule"].version == "1.0.0"
    assert lf.installed["my-rule"].path == ".claude/commands"
    assert lf.installed["http-request"].path is None


def test_load_missing_file_returns_default(tmp_path):
    lf = Lockfile.find(start=tmp_path)
    assert lf.source == DEFAULT_SOURCE
    assert lf.installed == {}
    assert lf.base_dir is None


# ---------------------------------------------------------------------------
# Lockfile.save — round-trip
# ---------------------------------------------------------------------------

def test_save_bare_string_for_default_path(tmp_path):
    """Items without a custom path should be saved as bare version strings."""
    lf = Lockfile(path=tmp_path / "skills.yaml", source=DEFAULT_SOURCE, installed={})
    lf.add("send-email", "1.0.0")
    lf.save()

    data = yaml.safe_load((tmp_path / "skills.yaml").read_text())
    assert data["installed"]["send-email"] == "1.0.0"


def test_save_dict_for_custom_path(tmp_path):
    lf = Lockfile(path=tmp_path / "skills.yaml", source=DEFAULT_SOURCE, installed={})
    lf.add("my-rule", "1.0.0", path=".claude/commands")
    lf.save()

    data = yaml.safe_load((tmp_path / "skills.yaml").read_text())
    assert data["installed"]["my-rule"] == {"version": "1.0.0", "path": ".claude/commands"}


def test_save_base_dir_when_set(tmp_path):
    lf = Lockfile(path=tmp_path / "skills.yaml", source=DEFAULT_SOURCE, installed={}, base_dir=".windsurf")
    lf.save()

    data = yaml.safe_load((tmp_path / "skills.yaml").read_text())
    assert data["base_dir"] == ".windsurf"


def test_save_omits_base_dir_when_none(tmp_path):
    lf = Lockfile(path=tmp_path / "skills.yaml", source=DEFAULT_SOURCE, installed={})
    lf.save()

    data = yaml.safe_load((tmp_path / "skills.yaml").read_text())
    assert "base_dir" not in data


def test_round_trip_mixed(tmp_path):
    lf_path = tmp_path / "skills.yaml"
    lf = Lockfile(path=lf_path, source="http://cat.example.com", installed={}, base_dir=".claude")
    lf.add("skill-a", "1.0.0")
    lf.add("skill-b", "2.0.0", path=".claude/commands")
    lf.save()

    lf2 = Lockfile.load(lf_path)
    assert lf2.source == "http://cat.example.com"
    assert lf2.base_dir == ".claude"
    assert lf2.installed["skill-a"].version == "1.0.0"
    assert lf2.installed["skill-a"].path is None
    assert lf2.installed["skill-b"].path == ".claude/commands"


# ---------------------------------------------------------------------------
# resolve_base_dir
# ---------------------------------------------------------------------------

def test_resolve_base_dir_default(tmp_path):
    lf = Lockfile(path=tmp_path / "skills.yaml", source=DEFAULT_SOURCE, installed={})
    assert lf.resolve_base_dir() == DEFAULT_BASE_DIR


def test_resolve_base_dir_custom(tmp_path):
    lf = Lockfile(path=tmp_path / "skills.yaml", source=DEFAULT_SOURCE, installed={}, base_dir=".claude")
    assert lf.resolve_base_dir() == ".claude"


# ---------------------------------------------------------------------------
# add / remove / has / helpers
# ---------------------------------------------------------------------------

def test_add_and_has(tmp_path):
    lf = Lockfile(path=tmp_path / "skills.yaml", source=DEFAULT_SOURCE, installed={})
    assert not lf.has("x")
    lf.add("x", "1.0.0")
    assert lf.has("x")
    assert lf.get_version("x") == "1.0.0"


def test_add_overwrites(tmp_path):
    lf = Lockfile(path=tmp_path / "skills.yaml", source=DEFAULT_SOURCE, installed={})
    lf.add("x", "1.0.0")
    lf.add("x", "2.0.0", path=".claude")
    assert lf.get_version("x") == "2.0.0"
    assert lf.get_path("x") == ".claude"


def test_remove(tmp_path):
    lf = Lockfile(path=tmp_path / "skills.yaml", source=DEFAULT_SOURCE, installed={})
    lf.add("x", "1.0.0")
    assert lf.remove("x") is True
    assert not lf.has("x")
    assert lf.remove("x") is False


def test_find_walks_up(tmp_path):
    """Lockfile.find should walk up directories to find skills.yaml."""
    lf_path = tmp_path / "skills.yaml"
    lf_path.write_text("source: http://example.com\ninstalled: {}\n", encoding="utf-8")
    subdir = tmp_path / "a" / "b"
    subdir.mkdir(parents=True)
    lf = Lockfile.find(start=subdir)
    assert lf.source == "http://example.com"
