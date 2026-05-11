"""Tests for skillsctl config command."""
from __future__ import annotations

from click.testing import CliRunner

from skillsctl.lockfile import DEFAULT_BASE_DIR, InstalledItem, Lockfile

from .conftest import invoke, make_client, make_lockfile


def test_config_base_dir_show_default(tmp_path):
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    client = make_client()

    result = invoke(runner, lf, client, "config", "base-dir")

    assert result.exit_code == 0, result.output
    assert DEFAULT_BASE_DIR in result.output
    assert "default" in result.output


def test_config_base_dir_show_custom(tmp_path):
    runner = CliRunner()
    lf = make_lockfile(tmp_path, base_dir=".claude")
    client = make_client()

    result = invoke(runner, lf, client, "config", "base-dir")

    assert result.exit_code == 0, result.output
    assert ".claude" in result.output
    assert "default" not in result.output


def test_config_base_dir_set(tmp_path):
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    client = make_client()

    result = invoke(runner, lf, client, "config", "base-dir", ".windsurf")

    assert result.exit_code == 0, result.output
    assert ".windsurf" in result.output
    lf2 = Lockfile.load(tmp_path / "skills.yaml")
    assert lf2.base_dir == ".windsurf"


def test_config_base_dir_unset(tmp_path):
    runner = CliRunner()
    lf = make_lockfile(tmp_path, base_dir=".claude")
    client = make_client()

    result = invoke(runner, lf, client, "config", "base-dir", "--unset")

    assert result.exit_code == 0, result.output
    lf2 = Lockfile.load(tmp_path / "skills.yaml")
    assert lf2.base_dir is None
    assert lf2.resolve_base_dir() == DEFAULT_BASE_DIR


def test_config_base_dir_persists_to_disk(tmp_path):
    """Setting base-dir must be written to skills.yaml immediately."""
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    client = make_client()

    invoke(runner, lf, client, "config", "base-dir", ".claude")

    lf2 = Lockfile.load(tmp_path / "skills.yaml")
    assert lf2.base_dir == ".claude"


def test_config_base_dir_set_moves_existing_files(tmp_path):
    """Changing base-dir relocates default-path installs to the new dir."""
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    lf.installed["http-request"] = InstalledItem(version="1.3.0")
    lf.installed["my-rule"] = InstalledItem(version="1.0.0", path=".claude/commands")
    lf.save()
    # Existing files: default-path one under .skillsctl/, custom-path one under .claude/commands/
    (tmp_path / ".skillsctl" / "skills").mkdir(parents=True)
    (tmp_path / ".skillsctl" / "skills" / "http-request.md").write_text("orig")
    (tmp_path / ".claude" / "commands").mkdir(parents=True)
    (tmp_path / ".claude" / "commands" / "my-rule.md").write_text("orig")
    client = make_client()

    result = invoke(runner, lf, client, "config", "base-dir", ".windsurf")

    assert result.exit_code == 0, result.output
    # Default-path file moved
    assert (tmp_path / ".windsurf" / "skills" / "http-request.md").read_text() == "orig"
    assert not (tmp_path / ".skillsctl" / "skills" / "http-request.md").exists()
    # Custom-path file untouched
    assert (tmp_path / ".claude" / "commands" / "my-rule.md").read_text() == "orig"
    assert "Moved 1 file" in result.output


def test_config_base_dir_unset_moves_existing_files(tmp_path):
    """--unset moves files back to the default base dir."""
    runner = CliRunner()
    lf = make_lockfile(tmp_path, base_dir=".claude")
    lf.installed["http-request"] = InstalledItem(version="1.3.0")
    lf.save()
    (tmp_path / ".claude" / "skills").mkdir(parents=True)
    (tmp_path / ".claude" / "skills" / "http-request.md").write_text("orig")
    client = make_client()

    result = invoke(runner, lf, client, "config", "base-dir", "--unset")

    assert result.exit_code == 0, result.output
    assert (tmp_path / DEFAULT_BASE_DIR / "skills" / "http-request.md").read_text() == "orig"
    assert not (tmp_path / ".claude" / "skills" / "http-request.md").exists()


def test_config_base_dir_no_files_to_move(tmp_path):
    """No 'Moved' line when nothing is on disk yet."""
    runner = CliRunner()
    lf = make_lockfile(tmp_path)
    client = make_client()

    result = invoke(runner, lf, client, "config", "base-dir", ".claude")

    assert result.exit_code == 0, result.output
    assert "Moved" not in result.output
    assert "Future installs will go to" in result.output
