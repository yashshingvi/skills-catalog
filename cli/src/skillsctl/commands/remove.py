"""skillsctl remove — remove installed items."""
from __future__ import annotations

import click
from rich.console import Console

from ..lockfile import Lockfile

console = Console()


@click.command("remove")
@click.argument("names", nargs=-1, required=True)
@click.pass_context
def remove(ctx: click.Context, names: tuple[str, ...]) -> None:
    """Remove installed skills, agents, rules, or workflows."""
    lockfile: Lockfile = ctx.obj["lockfile"]
    project_root = lockfile.path.parent
    base_dir = lockfile.resolve_base_dir()

    removed = 0
    for name in names:
        if not lockfile.has(name):
            console.print(f"[yellow]'{name}' is not installed, skipping[/]")
            continue

        entry = lockfile.installed[name]

        if entry.path is not None:
            candidates = [project_root / entry.path / f"{name}.md"]
        else:
            base = project_root / base_dir
            candidates = list(base.rglob(f"{name}.md")) if base.exists() else []

        found = False
        for md in candidates:
            if md.exists():
                md.unlink()
                found = True
                if entry.path is None:
                    parent = md.parent
                    base = project_root / base_dir
                    if parent != base and not any(parent.iterdir()):
                        parent.rmdir()

        lockfile.remove(name)
        removed += 1
        status = "removed" if found else "removed from lockfile (file not found)"
        console.print(f"  [red]- {name}[/] ({status})")

    lockfile.save()
    if removed:
        console.print(f"[green]{removed} item(s) removed.[/]")
