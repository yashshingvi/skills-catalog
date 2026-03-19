"""Git repo clone/pull for remote content sources."""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def _run_git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a git command, raising on failure."""
    cmd = ["git", *args]
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        logger.error("git %s failed: %s", " ".join(args), result.stderr.strip())
    return result


def ensure_repo(repo_url: str, branch: str, cache_dir: Path) -> Path:
    """
    Clone the repo if cache_dir doesn't exist; fetch + reset if it does.
    Returns cache_dir.
    """
    if cache_dir.exists() and (cache_dir / ".git").exists():
        logger.info("Updating existing clone at %s", cache_dir)
        _run_git("fetch", "origin", cwd=cache_dir)
        _run_git("reset", "--hard", f"origin/{branch}", cwd=cache_dir)
    else:
        cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Cloning %s (branch: %s) into %s", repo_url, branch, cache_dir)
        result = _run_git("clone", "--branch", branch, "--single-branch", repo_url, str(cache_dir))
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to clone {repo_url}: {result.stderr.strip()}"
            )
    return cache_dir


def pull_latest(cache_dir: Path, branch: str) -> bool:
    """
    Pull latest changes. Returns True if the HEAD changed.
    """
    old_sha = get_head_sha(cache_dir)
    _run_git("pull", "--ff-only", "origin", branch, cwd=cache_dir)
    new_sha = get_head_sha(cache_dir)
    changed = old_sha != new_sha
    if changed:
        logger.info("Content updated: %s → %s", old_sha[:8], new_sha[:8])
    return changed


def get_head_sha(cache_dir: Path) -> str:
    """Return the current HEAD commit SHA."""
    result = _run_git("rev-parse", "HEAD", cwd=cache_dir)
    return result.stdout.strip() if result.returncode == 0 else ""
