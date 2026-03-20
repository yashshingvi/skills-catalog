"""skillsctl sync — sync installed items to their catalog versions."""
from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from ..client import CatalogClient
from ..lockfile import Lockfile

console = Console()
SKILLS_DIR = ".skills"


@click.command("sync")
@click.pass_context
def sync(ctx: click.Context) -> None:
    """Re-download all installed items from the catalog (update to latest)."""
    client: CatalogClient = ctx.obj["client"]
    lockfile: Lockfile = ctx.obj["lockfile"]
    project_root = lockfile.path.parent

    if not lockfile.installed:
        console.print("[dim]Nothing to sync — no items in skills.yaml[/]")
        return

    updated = 0
    unchanged = 0
    errors = 0

    for name, entry in list(lockfile.installed.items()):
        item = client.get_item(name)
        if item is None:
            console.print(f"  [yellow]! {name}[/] — not found in catalog")
            errors += 1
            continue

        remote_version = item["version"]
        raw = client.get_raw(name)
        if raw is None:
            console.print(f"  [yellow]! {name}[/] — could not download")
            errors += 1
            continue

        # Respect the original install path stored in the lockfile
        if entry.path is not None:
            target_dir = project_root / entry.path
        else:
            target_dir = project_root / SKILLS_DIR / item["category"]

        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / f"{name}.md"
        target_file.write_text(raw, encoding="utf-8")
        lockfile.add(name, remote_version, path=entry.path)

        if entry.version != remote_version:
            console.print(f"  [green]+ {name}[/] {entry.version} → {remote_version}")
            updated += 1
        else:
            unchanged += 1

    lockfile.save()
    console.print(
        f"\n[green]{updated} updated[/], {unchanged} unchanged, "
        f"{'[yellow]' + str(errors) + ' errors[/]' if errors else '0 errors'}"
    )
