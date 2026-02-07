"""Technique management commands — backed by movements glossary."""

from datetime import date

import typer
from rich.console import Console
from rich.table import Table

from rivaflow.cli import prompts
from rivaflow.cli.utils.user_context import get_current_user_id
from rivaflow.core.services.glossary_service import GlossaryService

app = typer.Typer(help="Technique tracking and management")
console = Console()


@app.command()
def add(
    name: str = typer.Argument(..., help="Technique name"),
    category: str | None = typer.Option(
        None,
        "--category",
        "-c",
        help="Category (position, submission, sweep, pass, takedown, escape, movement, concept, defense)",
    ),
):
    """Add a technique to track (creates a glossary entry)."""
    user_id = get_current_user_id()
    service = GlossaryService()

    # Check if already exists
    existing = service.get_movement_by_name(user_id, name)
    if existing:
        prompts.print_info(f"Technique '{name}' already exists (ID: {existing['id']})")
        return

    # Add new technique as custom glossary entry
    movement = service.create_custom_movement(
        user_id=user_id,
        name=name,
        category=category or "submission",
    )

    prompts.print_success(f"Technique added (ID: {movement['id']})")


@app.command()
def list():
    """List all trained techniques."""
    user_id = get_current_user_id()
    service = GlossaryService()
    techniques = service.list_trained_movements(user_id, trained_only=True)

    if not techniques:
        console.print("[yellow]No techniques tracked yet[/yellow]")
        console.print("[dim]Log a session with techniques to see them here[/dim]")
        return

    console.print(f"[bold]Trained Techniques ({len(techniques)})[/bold]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Name", style="white", max_width=30)
    table.add_column("Category", style="cyan", max_width=15)
    table.add_column("Last Trained", style="yellow", width=12)
    table.add_column("Count", style="dim", width=6)

    for tech in techniques:
        last = tech.get("last_trained_date")
        last_str = str(last)[:10] if last else "Never"

        table.add_row(
            str(tech["id"]),
            tech["name"],
            tech.get("category", "—"),
            last_str,
            str(tech.get("train_count", 0)),
        )

    console.print(table)


@app.command()
def stale(
    days: int = typer.Option(7, "--days", "-d", help="Days threshold for stale"),
):
    """Show techniques not trained recently."""
    user_id = get_current_user_id()
    service = GlossaryService()
    stale_techniques = service.get_stale_movements(user_id, days=days)

    if not stale_techniques:
        prompts.print_success(f"No stale techniques! All trained within {days} days.")
        return

    console.print(
        f"[bold yellow]Stale Techniques[/bold yellow] "
        f"[dim](not trained in {days}+ days)[/dim]\n"
    )

    table = Table(show_header=True, header_style="bold yellow")
    table.add_column("Name", style="white", max_width=30)
    table.add_column("Category", style="cyan", max_width=15)
    table.add_column("Last Trained", style="yellow", width=12)
    table.add_column("Days Ago", style="red", width=8)

    today = date.today()
    for tech in stale_techniques:
        last = tech.get("last_trained_date")
        if last and isinstance(last, str):
            try:
                last_date = date.fromisoformat(last[:10])
                days_since = (today - last_date).days
            except ValueError:
                days_since = None
        else:
            days_since = None

        table.add_row(
            tech["name"],
            tech.get("category", "—"),
            str(last)[:10] if last else "Never",
            str(days_since) if days_since is not None else "—",
        )

    console.print(table)
    console.print()
    console.print(
        "[dim]Tip: Use 'rivaflow suggest' to get recommendations"
        " including stale techniques[/dim]"
    )


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
):
    """Search techniques by name."""
    user_id = get_current_user_id()
    service = GlossaryService()
    results = service.list_trained_movements(user_id, search=query)

    if not results:
        console.print(f"[yellow]No techniques found matching '{query}'[/yellow]")
        return

    console.print(f"[bold]Search results for '{query}':[/bold]\n")

    for tech in results:
        console.print(f"  {tech['name']} ({tech.get('category', '—')})")
