"""Readiness check-in commands."""
import typer
from datetime import date, datetime
from typing import Optional

from rivaflow.cli import prompts
from rivaflow.core.services.readiness_service import ReadinessService

app = typer.Typer(help="Daily readiness check-in")


@app.command()
def readiness(
    check_date: Optional[str] = typer.Option(
        None,
        "--date",
        "-d",
        help="Date for check-in (YYYY-MM-DD). Defaults to today.",
    ),
):
    """Log daily readiness check-in."""
    service = ReadinessService()

    # Parse date
    if check_date:
        try:
            target_date = datetime.strptime(check_date, "%Y-%m-%d").date()
        except ValueError:
            prompts.print_error("Invalid date format. Use YYYY-MM-DD")
            raise typer.Exit(1)
    else:
        target_date = date.today()

    # Check if already logged for this date
    existing = service.get_readiness(target_date)
    if existing:
        prompts.console.print(
            f"[yellow]Readiness already logged for {target_date}. Updating...[/yellow]\n"
        )

    # Prompt for readiness metrics
    prompts.console.print(f"[bold]Readiness Check-in: {target_date}[/bold]\n")

    sleep = prompts.prompt_int("How did you sleep? (1-5)", default=3, min_val=1, max_val=5)
    stress = prompts.prompt_int("Stress level? (1-5)", default=3, min_val=1, max_val=5)
    soreness = prompts.prompt_int("Soreness level? (1-5)", default=2, min_val=1, max_val=5)
    energy = prompts.prompt_int("Energy level? (1-5)", default=3, min_val=1, max_val=5)

    hotspot_note = prompts.prompt_text(
        "Any hotspots? (injury/soreness location, optional)"
    )
    if not hotspot_note:
        hotspot_note = None

    # Save readiness
    service.log_readiness(
        check_date=target_date,
        sleep=sleep,
        stress=stress,
        soreness=soreness,
        energy=energy,
        hotspot_note=hotspot_note,
    )

    # Display summary
    readiness_entry = service.get_readiness(target_date)
    prompts.console.print()
    prompts.console.print(service.format_readiness_summary(readiness_entry))
