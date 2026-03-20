"""skillsctl config — view and set project-level configuration."""
from __future__ import annotations

import click
from rich.console import Console

from ..lockfile import DEFAULT_BASE_DIR, Lockfile

console = Console()


@click.group("config")
def config() -> None:
    """View or set project-level skillsctl configuration."""


@config.command("base-dir")
@click.argument("directory", required=False, default=None)
@click.option("--unset", is_flag=True, help="Reset to the default (.skillsctl)")
@click.pass_context
def base_dir(ctx: click.Context, directory: str | None, unset: bool) -> None:
    """Get or set the default directory for installed files.

    \b
    Examples:
      skillsctl config base-dir             # show current value
      skillsctl config base-dir .claude     # set to .claude/{category}/{name}.md
      skillsctl config base-dir .windsurf   # set to .windsurf/{category}/{name}.md
      skillsctl config base-dir --unset     # reset to .skillsctl (default)
    """
    lockfile: Lockfile = ctx.obj["lockfile"]

    if unset:
        lockfile.base_dir = None
        lockfile.save()
        console.print(f"[green]base-dir reset to default:[/] {DEFAULT_BASE_DIR}/")
        return

    if directory is None:
        current = lockfile.base_dir
        if current is None:
            console.print(f"[dim]base-dir:[/] {DEFAULT_BASE_DIR}/ [dim](default)[/]")
        else:
            console.print(f"[dim]base-dir:[/] {current}/")
        return

    lockfile.base_dir = directory
    lockfile.save()
    console.print(f"[green]base-dir set to:[/] {directory}/")
    console.print(f"[dim]Future installs will go to {directory}/{{category}}/{{name}}.md[/]")
