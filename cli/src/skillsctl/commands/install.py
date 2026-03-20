"""skillsctl install — download and save items from the catalog."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from ..client import CatalogClient
from ..lockfile import Lockfile

console = Console()


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


def _target_file(
    project_root: Path,
    name: str,
    category: str,
    base_dir: str,
    custom_path: Optional[str],
) -> Path:
    """Resolve the destination file path for an item.

    custom_path (--path) overrides everything, placing the file flat with no
    category subfolder.  Otherwise files go to {base_dir}/{category}/{name}.md.
    """
    if custom_path is not None:
        return project_root / custom_path / f"{name}.md"
    return project_root / base_dir / category / f"{name}.md"


@click.command("install")
@click.argument("names", nargs=-1, required=True)
@click.option("--with-deps/--no-deps", default=True, help="Install required dependencies")
@click.option(
    "--path",
    "install_path",
    default=None,
    metavar="DIR",
    help=(
        "Write this item flat into DIR as {name}.md (no category subfolder). "
        "Overrides base-dir for this item only. "
        "Dependencies always use base-dir. "
        "To change the default for all installs use: skillsctl config base-dir <dir>"
    ),
)
@click.pass_context
def install(
    ctx: click.Context,
    names: tuple[str, ...],
    with_deps: bool,
    install_path: Optional[str],
) -> None:
    """Install skills, agents, rules, or workflows from the catalog."""
    client: CatalogClient = ctx.obj["client"]
    lockfile: Lockfile = ctx.obj["lockfile"]
    project_root = lockfile.path.parent
    base_dir = lockfile.resolve_base_dir()

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

    bundle = client.get_bundle(list(resolved.keys()))
    content_map = {bi["name"]: bi for bi in bundle["items"]}

    if bundle["errors"]:
        for err in bundle["errors"]:
            console.print(f"[yellow]Warning:[/] could not download '{err}'")

    installed: list[tuple[str, str, str, Path, bool]] = []

    for name, item_meta in resolved.items():
        if name not in content_map:
            continue
        bi = content_map[name]
        category = bi["category"]
        is_dep = name not in names

        # Dependencies always use base_dir; only explicit installs get --path
        effective_path = None if is_dep else install_path
        target_file = _target_file(project_root, name, category, base_dir, effective_path)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(bi["content"], encoding="utf-8")

        stored_path = effective_path  # keep as-is; no Path normalization (avoids \ on Windows)
        lockfile.add(name, bi["version"], path=stored_path)
        installed.append((name, bi["version"], category, target_file, is_dep))

    lockfile.save()

    table = Table(title="Installed", show_lines=False)
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Category", style="magenta")
    table.add_column("Path", style="dim")
    for name, version, category, path, is_dep in installed:
        label = f"{name} [dim](dep)[/]" if is_dep else name
        table.add_row(label, version, category, str(path.relative_to(project_root)))
    console.print(table)
    console.print(f"[green]{len(installed)} item(s) installed.[/]")
