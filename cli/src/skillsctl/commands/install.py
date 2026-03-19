"""skillsctl install — download and save items from the catalog."""
from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ..client import CatalogClient
from ..lockfile import Lockfile

console = Console()
SKILLS_DIR = ".skills"


def _resolve_deps(
    client: CatalogClient,
    names: list[str],
    resolved: dict[str, dict],
) -> None:
    """Recursively resolve requires dependencies."""
    for name in names:
        if name in resolved:
            continue
        item = client.get_item(name)
        if item is None:
            console.print(f"[yellow]Warning:[/] '{name}' not found in catalog, skipping")
            continue
        resolved[name] = item
        requires = item.get("requires", [])
        if requires:
            _resolve_deps(client, requires, resolved)


@click.command("install")
@click.argument("names", nargs=-1, required=True)
@click.option("--with-deps/--no-deps", default=True, help="Install required dependencies")
@click.pass_context
def install(ctx: click.Context, names: tuple[str, ...], with_deps: bool) -> None:
    """Install skills, agents, rules, or workflows from the catalog."""
    client: CatalogClient = ctx.obj["client"]
    lockfile: Lockfile = ctx.obj["lockfile"]
    project_root = lockfile.path.parent

    # Resolve all items (and deps if requested)
    resolved: dict[str, dict] = {}
    if with_deps:
        _resolve_deps(client, list(names), resolved)
    else:
        for name in names:
            item = client.get_item(name)
            if item is None:
                console.print(f"[yellow]Warning:[/] '{name}' not found in catalog, skipping")
                continue
            resolved[name] = item

    if not resolved:
        raise click.ClickException("No items to install.")

    # Download raw files via bundle endpoint for efficiency
    bundle = client.get_bundle(list(resolved.keys()))
    content_map = {bi["name"]: bi for bi in bundle["items"]}

    if bundle["errors"]:
        for err in bundle["errors"]:
            console.print(f"[yellow]Warning:[/] could not download '{err}'")

    # Write files and update lockfile
    installed: list[tuple[str, str, str, Path]] = []  # (name, version, category, path)

    for name, item_meta in resolved.items():
        if name not in content_map:
            continue
        bi = content_map[name]
        category = bi["category"]
        target_dir = project_root / SKILLS_DIR / category
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / f"{name}.md"
        target_file.write_text(bi["content"], encoding="utf-8")
        lockfile.add(name, bi["version"])
        installed.append((name, bi["version"], category, target_file))

    lockfile.save()

    # Summary table
    table = Table(title="Installed", show_lines=False)
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Category", style="magenta")
    table.add_column("Path", style="dim")
    for name, version, category, path in installed:
        is_dep = name not in names
        label = f"{name} [dim](dep)[/]" if is_dep else name
        table.add_row(label, version, category, str(path.relative_to(project_root)))
    console.print(table)
    console.print(f"[green]{len(installed)} item(s) installed.[/]")
