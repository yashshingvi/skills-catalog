"""skillsctl search — search the remote catalog."""
from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from ..client import CatalogClient

console = Console()


@click.command("search")
@click.argument("query")
@click.option("--category", "-c", default=None, help="Filter by category")
@click.option("--tag", "-t", default=None, help="Filter by tag")
@click.pass_context
def search(ctx: click.Context, query: str, category: str | None, tag: str | None) -> None:
    """Search the catalog for skills, agents, rules, or workflows."""
    client: CatalogClient = ctx.obj["client"]

    kwargs: dict = {}
    if category:
        kwargs["category"] = category
    if tag:
        kwargs["tags"] = tag

    result = client.search(query, **kwargs)

    if not result["results"]:
        console.print(f"[dim]No results for '{query}'[/]")
        return

    table = Table(title=f"Search: '{query}'", show_lines=False)
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Category", style="magenta")
    table.add_column("Description", max_width=50)

    for r in result["results"]:
        item = r["item"]
        desc = item["description"][:80] + ("..." if len(item["description"]) > 80 else "")
        table.add_row(item["name"], item["version"], item["category"], desc)

    console.print(table)
    console.print(f"[dim]{result['total']} result(s) found[/]")
