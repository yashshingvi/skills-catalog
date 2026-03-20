"""skillsctl remove — remove installed items."""
from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from ..lockfile import Lockfile

console = Console()
SKILLS_DIR = ".skills"


@click.command("remove")
@click.argument("names", nargs=-1, required=True)
@click.pass_context
def remove(ctx: click.Context, names: tuple[str, ...]) -> None:
    """Remove installed skills, agents, rules, or workflows."""
    lockfile: Lockfile = ctx.obj["lockfile"]
    project_root = lockfile.path.parent

    removed = 0
    for name in names:
        if not lockfile.has(name):
            console.print(f"[yellow]'{name}' is not installed, skipping[/]")
            continue

        entry = lockfile.installed[name]

        # Determine where the file lives based on lockfile metadata
        if entry.path is not None:
            # Custom install path — file is flat in that directory
            candidates = [project_root / entry.path / f"{name}.md"]
        else:
            # Default location — scan .skills/ subdirs (category unknown at remove time)
            skills_dir = project_root / SKILLS_DIR
            candidates = list(skills_dir.rglob(f"{name}.md"))

        found = False
        for md in candidates:
            if md.exists():
                md.unlink()
                found = True
                # Remove empty parent dirs (only for default .skills/ layout)
                if entry.path is None:
                    parent = md.parent
                    skills_dir = project_root / SKILLS_DIR
                    if parent != skills_dir and not any(parent.iterdir()):
                        parent.rmdir()

        lockfile.remove(name)
        removed += 1
        status = "removed" if found else "removed from lockfile (file not found)"
        console.print(f"  [red]- {name}[/] ({status})")

    lockfile.save()
    if removed:
        console.print(f"[green]{removed} item(s) removed.[/]")
