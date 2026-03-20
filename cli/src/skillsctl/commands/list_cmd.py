"""skillsctl list — show installed items."""
from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ..lockfile import Lockfile

console = Console()


@click.command("list")
@click.pass_context
def list_cmd(ctx: click.Context) -> None:
    """List all installed items from skills.yaml."""
    lockfile: Lockfile = ctx.obj["lockfile"]
    project_root = lockfile.path.parent
    base_dir = lockfile.resolve_base_dir()

    if not lockfile.installed:
        console.print("[dim]No items installed. Run 'skillsctl install <name>' to get started.[/]")
        return

    table = Table(title="Installed Items", show_lines=False)
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Path", style="dim")

    for name, entry in sorted(lockfile.installed.items()):
        if entry.path is not None:
            # Custom --path install: file is flat in that dir
            candidate = project_root / entry.path / f"{name}.md"
            path_str = str(candidate.relative_to(project_root)) if candidate.exists() else "[red]missing[/]"
        else:
            # Scan base_dir for the file (category subdir unknown at list time)
            base = project_root / base_dir
            matches = list(base.rglob(f"{name}.md")) if base.exists() else []
            path_str = str(matches[0].relative_to(project_root)) if matches else "[red]missing[/]"
        table.add_row(name, entry.version, path_str)

    console.print(table)
    console.print(f"[dim]Source: {lockfile.source}[/]")
    if lockfile.base_dir:
        console.print(f"[dim]Base dir: {lockfile.base_dir}/[/]")
