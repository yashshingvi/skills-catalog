"""skillsctl list — show installed items."""
from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ..lockfile import Lockfile

console = Console()
SKILLS_DIR = ".skills"


@click.command("list")
@click.pass_context
def list_cmd(ctx: click.Context) -> None:
    """List all installed items from skills.yaml."""
    lockfile: Lockfile = ctx.obj["lockfile"]
    project_root = lockfile.path.parent
    skills_dir = project_root / SKILLS_DIR

    if not lockfile.installed:
        console.print("[dim]No items installed. Run 'skillsctl install <name>' to get started.[/]")
        return

    table = Table(title="Installed Items", show_lines=False)
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Path", style="dim")

    for name, version in sorted(lockfile.installed.items()):
        # Find the file to show path
        matches = list(skills_dir.rglob(f"{name}.md")) if skills_dir.exists() else []
        path_str = str(matches[0].relative_to(project_root)) if matches else "[red]missing[/]"
        table.add_row(name, version, path_str)

    console.print(table)
    console.print(f"[dim]Source: {lockfile.source}[/]")
