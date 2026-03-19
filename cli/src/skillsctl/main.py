"""Main CLI group for skillsctl."""
from __future__ import annotations

import os

import click

from . import __version__
from .client import CatalogClient
from .lockfile import Lockfile


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

    # Source resolution: --source flag > skills.yaml > env var > default
    resolved_source = source or lockfile.source
    lockfile.source = resolved_source

    ctx.obj["lockfile"] = lockfile
    ctx.obj["client"] = CatalogClient(resolved_source)


# Register commands
from .commands.install import install
from .commands.remove import remove
from .commands.list_cmd import list_cmd
from .commands.search import search
from .commands.sync import sync
from .commands.update import update

cli.add_command(install)
cli.add_command(remove)
cli.add_command(list_cmd)
cli.add_command(search)
cli.add_command(sync)
cli.add_command(update)
