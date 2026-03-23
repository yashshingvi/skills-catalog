"""Main CLI group for skillsctl."""
from __future__ import annotations

import os

import click
from rich.console import Console
from rich.prompt import Prompt

from . import __version__
from .client import CatalogClient
from .lockfile import DEFAULT_BASE_DIR, Lockfile

# Subcommands that don't need a catalog server — skip first-run prompt for these.
_NO_SOURCE_COMMANDS = {"list", "remove", "config"}

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="skillsctl")
@click.option(
    "--source",
    envvar="SKILLSCTL_SOURCE",
    default=None,
    help="Catalog server URL (default: from skills.yaml or http://localhost:8000)",
)
@click.pass_context
def cli(ctx: click.Context, source: str | None) -> None:
    """Enterprise Skills Catalog CLI — install, manage, and search skills."""
    ctx.ensure_object(dict)

    lockfile = Lockfile.find()
    is_first_run = not lockfile.path.exists()

    # First-run setup: prompt when no skills.yaml exists and no source provided
    if (
        is_first_run
        and source is None
        and not os.environ.get("SKILLSCTL_SOURCE")
        and ctx.invoked_subcommand not in _NO_SOURCE_COMMANDS
    ):
        console.print("\n[bold cyan]Welcome to skillsctl![/bold cyan] Let's get you set up.\n")

        source_input = Prompt.ask(
            "[bold]Catalog source URL[/bold]",
            default="http://localhost:8000",
        )
        base_dir_input = Prompt.ask(
            "[bold]Default install directory[/bold] (where skill files are saved)",
            default=DEFAULT_BASE_DIR,
        )

        lockfile.source = source_input
        lockfile.base_dir = base_dir_input if base_dir_input != DEFAULT_BASE_DIR else None
        lockfile.save()

        console.print(
            f"\n[green]Config saved to skills.yaml.[/green] "
            f"Files will be installed to [bold]{base_dir_input}/{{category}}/[/bold]\n"
        )
        source = source_input

    # Source resolution: --source flag > skills.yaml > env var > default
    resolved_source = source or lockfile.source
    lockfile.source = resolved_source

    ctx.obj["lockfile"] = lockfile
    ctx.obj["client"] = CatalogClient(resolved_source)


# Register commands
from .commands.config import config
from .commands.install import install
from .commands.remove import remove
from .commands.list_cmd import list_cmd
from .commands.search import search
from .commands.sync import sync
from .commands.update import update

cli.add_command(config)
cli.add_command(install)
cli.add_command(remove)
cli.add_command(list_cmd)
cli.add_command(search)
cli.add_command(sync)
cli.add_command(update)
