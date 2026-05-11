"""skillsctl config — view and set project-level configuration."""
from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from ..lockfile import DEFAULT_BASE_DIR, Lockfile

console = Console()


def _migrate_default_files(
    lockfile: Lockfile, old_base: str, new_base: str
) -> int:
    """Move default-path installs from old_base/{cat}/{name}.md to new_base/{cat}/{name}.md.

    Items with an explicit `path` (--path installs) are untouched. Returns the
    number of files moved.
    """
    if old_base == new_base:
        return 0
    project_root = lockfile.path.parent
    old_root = project_root / old_base
    if not old_root.is_dir():
        return 0

    moved = 0
    for name, item in lockfile.installed.items():
        if item.path is not None:
            continue
        for existing in old_root.glob(f"*/{name}.md"):
            category = existing.parent.name
            new_target = project_root / new_base / category / f"{name}.md"
            if new_target.resolve() == existing.resolve():
                continue
            new_target.parent.mkdir(parents=True, exist_ok=True)
            existing.replace(new_target)
            moved += 1
            # Clean up empty category dir we just emptied
            try:
                existing.parent.rmdir()
            except OSError:
                pass
    # Clean up old base dir if now empty
    try:
        old_root.rmdir()
    except OSError:
        pass
    return moved


@click.group("config")
def config() -> None:
    """View or set project-level skillsctl configuration."""


@config.command("base-dir")
@click.argument("directory", required=False, default=None)
@click.option("--unset", is_flag=True, help="Reset to the default (.skillsctl)")
@click.pass_context
def base_dir(ctx: click.Context, directory: str | None, unset: bool) -> None:
    """Get or set the default directory for installed files.

    \b
    Examples:
      skillsctl config base-dir             # show current value
      skillsctl config base-dir .claude     # set to .claude/{category}/{name}.md
      skillsctl config base-dir .windsurf   # set to .windsurf/{category}/{name}.md
      skillsctl config base-dir --unset     # reset to .skillsctl (default)
    """
    lockfile: Lockfile = ctx.obj["lockfile"]

    if unset:
        old_base = lockfile.resolve_base_dir()
        lockfile.base_dir = None
        new_base = lockfile.resolve_base_dir()
        moved = _migrate_default_files(lockfile, old_base, new_base)
        lockfile.save()
        console.print(f"[green]base-dir reset to default:[/] {DEFAULT_BASE_DIR}/")
        if moved:
            console.print(f"[dim]Moved {moved} file(s) from {old_base}/ to {new_base}/[/]")
        return

    if directory is None:
        current = lockfile.base_dir
        if current is None:
            console.print(f"[dim]base-dir:[/] {DEFAULT_BASE_DIR}/ [dim](default)[/]")
        else:
            console.print(f"[dim]base-dir:[/] {current}/")
        return

    old_base = lockfile.resolve_base_dir()
    lockfile.base_dir = directory
    new_base = lockfile.resolve_base_dir()
    moved = _migrate_default_files(lockfile, old_base, new_base)
    lockfile.save()
    console.print(f"[green]base-dir set to:[/] {directory}/")
    if moved:
        console.print(f"[dim]Moved {moved} file(s) from {old_base}/ to {new_base}/[/]")
    else:
        console.print(f"[dim]Future installs will go to {directory}/{{category}}/{{name}}.md[/]")
