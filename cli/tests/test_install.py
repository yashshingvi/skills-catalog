"""Tests for skillsctl install command."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from skillsctl.commands.install import _target_file
from skillsctl.lockfile import DEFAULT_BASE_DIR, Lockfile

from .conftest import invoke, make_client, make_lockfile


# ---------------------------------------------------------------------------
# _target_file helper
# ---------------------------------------------------------------------------

def test_target_file_default(tmp_path):
    f = _target_file(tmp_path, "send-email", "skills", DEFAULT_BASE_DIR, None)
    assert f == tmp_path / DEFAULT_BASE_DIR / "skills" / "send-email.md"


def test_target_file_custom_base_dir(tmp_path):
    f = _target_file(tmp_path, "my-rule", "rules", ".claude", None)
    assert f == tmp_path / ".claude" / "rules" / "my-rule.md"


def test_target_file_with_path_override(tmp_path):
    """--path puts file flat in that dir, no category subfolder."""
    f = _target_file(tmp_path, "send-email", "skills", DEFAULT_BASE_DIR, ".claude/commands")
    assert f.name == "send-email.md"
    assert "skills" not in str(f)
    assert ".claude/commands" in str(f).replace("\\", "/")


# ---------------------------------------------------------------------------
# install — default path
# ---------------------------------------------------------------------------

def test_install_default_path(tmp_path, catalog_items):
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    client = make_client(catalog_items)

    result = invoke(runner, lf, client, "install", "--no-deps", "send-email")

    assert result.exit_code == 0, result.output
    expected = tmp_path / DEFAULT_BASE_DIR / "skills" / "send-email.md"
    assert expected.exists()
    lf2 = Lockfile.load(tmp_path / "skills.yaml")
    assert lf2.has("send-email")
    assert lf2.get_path("send-email") is None


def test_install_creates_category_subdir(tmp_path, catalog_items):
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    client = make_client(catalog_items)

    invoke(runner, lf, client, "install", "--no-deps", "my-agent")

    assert (tmp_path / DEFAULT_BASE_DIR / "agents" / "my-agent.md").exists()


# ---------------------------------------------------------------------------
# install — with --path override
# ---------------------------------------------------------------------------

def test_install_with_path(tmp_path, catalog_items):
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    client = make_client(catalog_items)

    result = invoke(runner, lf, client, "install", "--no-deps", "send-email", "--path", ".claude/commands")

    assert result.exit_code == 0, result.output
    assert (tmp_path / ".claude" / "commands" / "send-email.md").exists()
    lf2 = Lockfile.load(tmp_path / "skills.yaml")
    assert lf2.get_path("send-email") == ".claude/commands"


def test_install_path_no_category_subfolder(tmp_path, catalog_items):
    """--path must not add a category folder inside the target dir."""
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    client = make_client(catalog_items)

    invoke(runner, lf, client, "install", "--no-deps", "send-email", "--path", "out")

    assert (tmp_path / "out" / "send-email.md").exists()
    # should NOT exist
    assert not (tmp_path / "out" / "skills" / "send-email.md").exists()


# ---------------------------------------------------------------------------
# install — with base_dir configured
# ---------------------------------------------------------------------------

def test_install_uses_base_dir(tmp_path, catalog_items):
    runner = CliRunner()
    lf = make_lockfile(tmp_path, base_dir=".windsurf")
    client = make_client(catalog_items)

    invoke(runner, lf, client, "install", "--no-deps", "my-rule")

    assert (tmp_path / ".windsurf" / "rules" / "my-rule.md").exists()
    assert not (tmp_path / DEFAULT_BASE_DIR / "rules" / "my-rule.md").exists()


# ---------------------------------------------------------------------------
# install — with deps
# ---------------------------------------------------------------------------

def test_install_with_deps(tmp_path, catalog_items):
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    client = make_client(catalog_items)

    result = invoke(runner, lf, client, "install", "--with-deps", "my-agent")

    assert result.exit_code == 0, result.output
    # agent itself
    assert (tmp_path / DEFAULT_BASE_DIR / "agents" / "my-agent.md").exists()
    # dependency
    assert (tmp_path / DEFAULT_BASE_DIR / "skills" / "http-request.md").exists()


def test_deps_ignore_path_flag(tmp_path, catalog_items):
    """Dependencies should go to base_dir, NOT to --path."""
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    client = make_client(catalog_items)

    invoke(runner, lf, client, "install", "--with-deps", "my-agent", "--path", "custom")

    # explicit item gets --path
    assert (tmp_path / "custom" / "my-agent.md").exists()
    # dependency uses base_dir
    assert (tmp_path / DEFAULT_BASE_DIR / "skills" / "http-request.md").exists()
    assert not (tmp_path / "custom" / "http-request.md").exists()


# ---------------------------------------------------------------------------
# install — unknown item
# ---------------------------------------------------------------------------

def test_install_unknown_item(tmp_path, catalog_items):
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    client = make_client(catalog_items)

    result = invoke(runner, lf, client, "install", "--no-deps", "does-not-exist")

    assert result.exit_code != 0
