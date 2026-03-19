"""skillsctl update — update a specific item to the latest version."""
from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from ..client import CatalogClient
from ..lockfile import Lockfile

console = Console()
SKILLS_DIR = ".skills"


@click.command("update")
@click.argument("names", nargs=-1, required=True)
@click.pass_context
def update(ctx: click.Context, names: tuple[str, ...]) -> None:
    """Update specific installed items to their latest catalog version."""
    client: CatalogClient = ctx.obj["client"]
    lockfile: Lockfile = ctx.obj["lockfile"]
    project_root = lockfile.path.parent

    for name in names:
        if not lockfile.has(name):
            console.print(f"[yellow]'{name}' is not installed — use 'skillsctl install {name}' first[/]")
            continue

        local_version = lockfile.installed[name]
        item = client.get_item(name)
        if item is None:
            console.print(f"[yellow]'{name}' not found in catalog[/]")
            continue

        remote_version = item["version"]
        if local_version == remote_version:
            console.print(f"  [dim]{name} already at {local_version} (latest)[/]")
            continue

        raw = client.get_raw(name)
        if raw is None:
            console.print(f"[yellow]'{name}' — could not download[/]")
            continue

        category = item["category"]
        target_dir = project_root / SKILLS_DIR / category
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / f"{name}.md"
        target_file.write_text(raw, encoding="utf-8")
        lockfile.add(name, remote_version)
        console.print(f"  [green]+ {name}[/] {local_version} → {remote_version}")

    lockfile.save()
