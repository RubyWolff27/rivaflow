"""Report and analytics commands."""
import typer
from datetime import date, datetime
from typing import Optional
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from rivaflow.core.services.report_service import ReportService
from rivaflow.cli import prompts

app = typer.Typer(help="Training reports and analytics")
console = Console()


@app.command()
def week(
    csv: bool = typer.Option(False, "--csv", help="Export to CSV"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="CSV output file"),
):
    """Show current week report (Monday-Sunday)."""
    service = ReportService()
    start_date, end_date = service.get_week_dates()

    report = service.generate_report(start_date, end_date)

    if csv or output:
        _export_csv(service, report, output or "week_report.csv")
    else:
        _display_report(report, "WEEKLY REPORT")


@app.command()
def month(
    csv: bool = typer.Option(False, "--csv", help="Export to CSV"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="CSV output file"),
):
    """Show current month report."""
    service = ReportService()
    start_date, end_date = service.get_month_dates()

    report = service.generate_report(start_date, end_date)

    if csv or output:
        _export_csv(service, report, output or "month_report.csv")
    else:
        _display_report(report, "MONTHLY REPORT")


@app.command()
def range(
    start: str = typer.Argument(..., help="Start date (YYYY-MM-DD)"),
    end: str = typer.Argument(..., help="End date (YYYY-MM-DD)"),
    csv: bool = typer.Option(False, "--csv", help="Export to CSV"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="CSV output file"),
):
    """Show report for custom date range."""
    service = ReportService()

    # Parse dates
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
    except ValueError:
        prompts.print_error("Invalid date format. Use YYYY-MM-DD")
        raise typer.Exit(1)

    if start_date > end_date:
        prompts.print_error("Start date must be before end date")
        raise typer.Exit(1)

    report = service.generate_report(start_date, end_date)

    if csv or output:
        _export_csv(service, report, output or "range_report.csv")
    else:
        _display_report(report, "CUSTOM RANGE REPORT")


def _display_report(report: dict, title: str):
    """Display report with Rich tables."""
    # Header
    header = Panel(
        f"[bold]{title}[/bold]\n{report['start_date']} → {report['end_date']}",
        border_style="blue",
        padding=(0, 2),
    )
    console.print(header)
    console.print()

    # Check if no data
    if report["summary"]["total_classes"] == 0:
        console.print("[yellow]No sessions logged for this period[/yellow]")
        return

    # Summary table
    console.print("[bold]SUMMARY[/bold]")
    summary_table = Table(show_header=True, header_style="bold cyan", box=None)
    summary_table.add_column("Metric", style="dim")
    summary_table.add_column("Value", style="white")

    summary = report["summary"]
    summary_table.add_row("Total Classes", str(summary["total_classes"]))
    summary_table.add_row("Total Hours", str(summary["total_hours"]))
    summary_table.add_row("Total Rolls", str(summary["total_rolls"]))
    summary_table.add_row("Unique Partners", str(summary["unique_partners"]))
    summary_table.add_row("Submissions For", str(summary["submissions_for"]))
    summary_table.add_row("Submissions Against", str(summary["submissions_against"]))
    summary_table.add_row("Avg Intensity", str(summary["avg_intensity"]))

    console.print(summary_table)
    console.print()

    # Rates table
    console.print("[bold]RATES[/bold]")
    rates_table = Table(show_header=True, header_style="bold cyan", box=None)
    rates_table.add_column("Rate", style="dim")
    rates_table.add_column("Value", style="white")

    rates_table.add_row("Subs per Class", str(summary["subs_per_class"]))
    rates_table.add_row("Subs per Roll", str(summary["subs_per_roll"]))
    rates_table.add_row("Taps per Roll", str(summary["taps_per_roll"]))
    rates_table.add_row("Sub Ratio (F:A)", str(summary["sub_ratio"]))

    console.print(rates_table)
    console.print()

    # Breakdown by type
    if report["breakdown_by_type"]:
        console.print("[bold]BREAKDOWN BY TYPE[/bold]")
        type_table = Table(show_header=True, header_style="bold cyan", box=None)
        type_table.add_column("Type", style="white")
        type_table.add_column("Classes", style="cyan")
        type_table.add_column("Hours", style="cyan")
        type_table.add_column("Rolls", style="cyan")

        for class_type, data in sorted(report["breakdown_by_type"].items()):
            type_table.add_row(
                class_type.upper(),
                str(data["classes"]),
                str(data["hours"]),
                str(data["rolls"]),
            )

        console.print(type_table)
        console.print()

    # Breakdown by gym
    if report["breakdown_by_gym"]:
        console.print("[bold]BREAKDOWN BY GYM[/bold]")
        gym_table = Table(show_header=True, header_style="bold cyan", box=None)
        gym_table.add_column("Gym", style="white")
        gym_table.add_column("Classes", style="cyan")

        for gym, count in sorted(
            report["breakdown_by_gym"].items(), key=lambda x: x[1], reverse=True
        ):
            gym_table.add_row(gym, str(count))

        console.print(gym_table)


def _export_csv(service: ReportService, report: dict, filename: str):
    """Export report data to CSV."""
    output_path = Path(filename)
    service.export_to_csv(report["sessions"], str(output_path))
    prompts.print_success(f"Report exported to {output_path}")
