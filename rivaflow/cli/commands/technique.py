"""Technique management commands."""
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table

from rivaflow.cli.utils.user_context import get_current_user_id
from rivaflow.core.services.technique_service import TechniqueService
from rivaflow.cli import prompts

app = typer.Typer(help="Technique tracking and management")
console = Console()


@app.command()
def add(
    name: str = typer.Argument(..., help="Technique name"),
    category: Optional[str] = typer.Option(
        None,
        "--category",
        "-c",
        help="Category (guard, pass, submission, sweep, takedown, escape, position)",
    ),
):
    """Add a technique to track."""
    user_id = get_current_user_id()
    service = TechniqueService()

    # Check if already exists
    existing = service.get_technique_by_name(user_id, name)
    if existing:
        prompts.print_info(f"Technique '{name}' already exists (ID: {existing['id']})")
        console.print()
        console.print(service.format_technique_summary(existing))
        return

    # Add new technique
    technique_id = service.add_technique(user_id, name=name, category=category)
    technique = service.get_technique(user_id, technique_id)

    prompts.print_success(f"Technique added (ID: {technique_id})")
    console.print()
    console.print(service.format_technique_summary(technique))


@app.command()
def list():
    """List all tracked techniques."""
    user_id = get_current_user_id()
    service = TechniqueService()
    techniques = service.list_all_techniques(user_id)

    if not techniques:
        console.print("[yellow]No techniques tracked yet[/yellow]")
        console.print("[dim]Add techniques with 'rivaflow technique add <name>'[/dim]")
        return

    console.print(f"[bold]Tracked Techniques ({len(techniques)})[/bold]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Name", style="white", max_width=30)
    table.add_column("Category", style="cyan", max_width=15)
    table.add_column("Last Trained", style="yellow", width=12)
    table.add_column("Days Ago", style="dim", width=8)

    for tech in techniques:
        days_since = service.calculate_days_since_trained(tech)

        table.add_row(
            str(tech["id"]),
            tech["name"],
            tech.get("category", "—"),
            str(tech.get("last_trained_date", "Never"))[:10],
            str(days_since) if days_since is not None else "—",
        )

    console.print(table)


@app.command()
def stale(
    days: int = typer.Option(7, "--days", "-d", help="Days threshold for stale"),
):
    """Show techniques not trained recently."""
    service = TechniqueService()
    stale_techniques = service.get_stale_techniques(days)

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

    for tech in stale_techniques:
        days_since = service.calculate_days_since_trained(tech)

        table.add_row(
            tech["name"],
            tech.get("category", "—"),
            str(tech.get("last_trained_date", "Never"))[:10],
            str(days_since) if days_since is not None else "∞",
        )

    console.print(table)
    console.print()
    console.print(
        f"[dim]💡 Tip: Use 'rivaflow suggest' to get recommendations including stale techniques[/dim]"
    )


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
):
    """Search techniques by name."""
    service = TechniqueService()
    results = service.search_techniques(query)

    if not results:
        console.print(f"[yellow]No techniques found matching '{query}'[/yellow]")
        return

    console.print(f"[bold]Search results for '{query}':[/bold]\n")

    for tech in results:
        console.print(service.format_technique_summary(tech))
        console.print()
