"""Tests for skillsctl config command."""
from __future__ import annotations

from click.testing import CliRunner

from skillsctl.lockfile import DEFAULT_BASE_DIR, Lockfile

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
