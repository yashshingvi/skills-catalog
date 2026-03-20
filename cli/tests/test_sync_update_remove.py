"""Tests for sync, update, and remove commands."""
from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from skillsctl.lockfile import DEFAULT_BASE_DIR, Lockfile

from .conftest import invoke, make_client, make_lockfile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _plant_file(project_root: Path, rel: str, content: str = "old content") -> Path:
    """Write a file relative to project_root and return its Path."""
    target = project_root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# sync
# ---------------------------------------------------------------------------

def test_sync_empty(tmp_path):
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    result = invoke(runner, lf, make_client(), "sync")
    assert result.exit_code == 0
    assert "Nothing to sync" in result.output


def test_sync_default_path(tmp_path, catalog_items):
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    lf.add("send-email", "0.9.0")          # outdated
    lf.save()
    _plant_file(tmp_path, f"{DEFAULT_BASE_DIR}/skills/send-email.md", "old")

    result = invoke(runner, lf, make_client(catalog_items), "sync")

    assert result.exit_code == 0, result.output
    updated_file = tmp_path / DEFAULT_BASE_DIR / "skills" / "send-email.md"
    assert updated_file.exists()
    assert "send-email" in result.output


def test_sync_respects_base_dir(tmp_path, catalog_items):
    runner = CliRunner()
    lf = make_lockfile(tmp_path, base_dir=".windsurf")
    lf.add("my-rule", "0.1.0")
    lf.save()

    result = invoke(runner, lf, make_client(catalog_items), "sync")

    assert result.exit_code == 0, result.output
    assert (tmp_path / ".windsurf" / "rules" / "my-rule.md").exists()
    assert not (tmp_path / DEFAULT_BASE_DIR / "rules" / "my-rule.md").exists()


def test_sync_respects_stored_path(tmp_path, catalog_items):
    """Items installed with --path must sync back to the same custom path."""
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    lf.add("send-email", "0.9.0", path=".claude/commands")
    lf.save()

    result = invoke(runner, lf, make_client(catalog_items), "sync")

    assert result.exit_code == 0, result.output
    assert (tmp_path / ".claude" / "commands" / "send-email.md").exists()
    assert not (tmp_path / DEFAULT_BASE_DIR / "skills" / "send-email.md").exists()


def test_sync_unchanged_count(tmp_path, catalog_items):
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    lf.add("send-email", "1.0.0")   # already at latest
    lf.save()
    _plant_file(tmp_path, f"{DEFAULT_BASE_DIR}/skills/send-email.md")

    result = invoke(runner, lf, make_client(catalog_items), "sync")

    assert "0 errors" in result.output
    assert "1 unchanged" in result.output


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

def test_update_not_installed(tmp_path, catalog_items):
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    result = invoke(runner, lf, make_client(catalog_items), "update", "send-email")
    assert result.exit_code == 0
    assert "not installed" in result.output


def test_update_already_latest(tmp_path, catalog_items):
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    lf.add("send-email", "1.0.0")
    lf.save()
    _plant_file(tmp_path, f"{DEFAULT_BASE_DIR}/skills/send-email.md")

    result = invoke(runner, lf, make_client(catalog_items), "update", "send-email")

    assert "already at" in result.output


def test_update_upgrades_file(tmp_path, catalog_items):
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    lf.add("send-email", "0.1.0")
    lf.save()
    old_file = _plant_file(tmp_path, f"{DEFAULT_BASE_DIR}/skills/send-email.md", "old")

    result = invoke(runner, lf, make_client(catalog_items), "update", "send-email")

    assert result.exit_code == 0, result.output
    assert old_file.exists()
    assert "0.1.0" in result.output
    lf2 = Lockfile.load(tmp_path / "skills.yaml")
    assert lf2.get_version("send-email") == "1.0.0"


def test_update_respects_base_dir(tmp_path, catalog_items):
    runner = CliRunner()
    lf = make_lockfile(tmp_path, base_dir=".windsurf")
    lf.add("my-rule", "0.1.0")
    lf.save()

    invoke(runner, lf, make_client(catalog_items), "update", "my-rule")

    assert (tmp_path / ".windsurf" / "rules" / "my-rule.md").exists()


def test_update_respects_stored_path(tmp_path, catalog_items):
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    lf.add("send-email", "0.1.0", path=".claude/commands")
    lf.save()

    invoke(runner, lf, make_client(catalog_items), "update", "send-email")

    assert (tmp_path / ".claude" / "commands" / "send-email.md").exists()
    assert not (tmp_path / DEFAULT_BASE_DIR / "skills" / "send-email.md").exists()


# ---------------------------------------------------------------------------
# remove
# ---------------------------------------------------------------------------

def test_remove_not_installed(tmp_path):
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    result = invoke(runner, lf, make_client(), "remove", "does-not-exist")
    assert result.exit_code == 0
    assert "not installed" in result.output


def test_remove_default_path(tmp_path, catalog_items):
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    lf.add("send-email", "1.0.0")
    lf.save()
    md = _plant_file(tmp_path, f"{DEFAULT_BASE_DIR}/skills/send-email.md")

    result = invoke(runner, lf, make_client(), "remove", "send-email")

    assert result.exit_code == 0, result.output
    assert not md.exists()
    assert not Lockfile.load(tmp_path / "skills.yaml").has("send-email")


def test_remove_cleans_empty_category_dir(tmp_path, catalog_items):
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    lf.add("send-email", "1.0.0")
    lf.save()
    _plant_file(tmp_path, f"{DEFAULT_BASE_DIR}/skills/send-email.md")

    invoke(runner, lf, make_client(), "remove", "send-email")

    # empty category dir should be removed
    assert not (tmp_path / DEFAULT_BASE_DIR / "skills").exists()


def test_remove_custom_path(tmp_path):
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    lf.add("my-rule", "1.0.0", path=".claude/commands")
    lf.save()
    md = _plant_file(tmp_path, ".claude/commands/my-rule.md")

    result = invoke(runner, lf, make_client(), "remove", "my-rule")

    assert result.exit_code == 0, result.output
    assert not md.exists()
    assert not Lockfile.load(tmp_path / "skills.yaml").has("my-rule")


def test_remove_custom_path_does_not_scan_base_dir(tmp_path):
    """remove with a stored custom path should NOT touch .skillsctl/."""
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    lf.add("my-rule", "1.0.0", path=".claude/commands")
    lf.save()
    # put a file in the default location (shouldn't be touched)
    decoy = _plant_file(tmp_path, f"{DEFAULT_BASE_DIR}/rules/my-rule.md")

    invoke(runner, lf, make_client(), "remove", "my-rule")

    # decoy must still exist — remove only targets the stored path
    assert decoy.exists()


def test_remove_file_missing_still_removes_from_lockfile(tmp_path):
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    lf.add("send-email", "1.0.0")
    lf.save()
    # no file on disk

    result = invoke(runner, lf, make_client(), "remove", "send-email")

    assert result.exit_code == 0
    assert "lockfile" in result.output
    assert not Lockfile.load(tmp_path / "skills.yaml").has("send-email")
