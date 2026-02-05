"""Report and analytics commands."""

from datetime import datetime
from pathlib import Path

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from rivaflow.cli import prompts
from rivaflow.core.services.report_service import ReportService

app = typer.Typer(help="Training reports and analytics")
console = Console()


@app.command()
def week(
    csv: bool = typer.Option(False, "--csv", help="Export to CSV"),
    output: str | None = typer.Option(None, "--output", "-o", help="CSV output file"),
):
    """
    Show current week training report (Monday-Sunday).

    \b
    Displays:
      • Total sessions and hours
      • Average intensity
      • Rolls and submissions
      • Class type breakdown
      • Daily session list

    \b
    Examples:
      # View week report
      $ rivaflow report week

      # Export to CSV
      $ rivaflow report week --csv
      $ rivaflow report week --output my_week.csv
    """
    service = ReportService()
    start_date, end_date = service.get_week_dates()

    with console.status("[cyan]Generating weekly report...", spinner="dots"):
        report = service.generate_report(start_date, end_date)

    if csv or output:
        _export_csv(service, report, output or "week_report.csv")
    else:
        _display_report(report, "WEEKLY REPORT")


@app.command()
def month(
    csv: bool = typer.Option(False, "--csv", help="Export to CSV"),
    output: str | None = typer.Option(None, "--output", "-o", help="CSV output file"),
):
    """
    Show current month training report.

    \b
    Monthly summary including:
      • Training volume and trends
      • Performance metrics
      • Weekly comparison
      • Top techniques

    \b
    Examples:
      # View month report
      $ rivaflow report month

      # Export month data
      $ rivaflow report month --csv
    """
    service = ReportService()
    start_date, end_date = service.get_month_dates()

    with console.status("[cyan]Generating monthly report...", spinner="dots"):
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
    output: str | None = typer.Option(None, "--output", "-o", help="CSV output file"),
):
    """
    Show training report for custom date range.

    \b
    Create reports for any time period:
      • Belt promotion periods
      • Training camps
      • Competition prep cycles
      • Injury recovery periods

    \b
    Examples:
      # Last 30 days
      $ rivaflow report range 2026-01-03 2026-02-02

      # Competition prep (3 months)
      $ rivaflow report range 2025-11-01 2026-02-01

      # Export belt period
      $ rivaflow report range 2025-06-01 2025-12-31 --csv
    """
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

    with console.status("[cyan]Generating custom range report...", spinner="dots"):
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
    console.print("[bold cyan]TRAINING SUMMARY[/bold cyan]")
    summary_table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
    summary_table.add_column("Metric", style="dim", width=20)
    summary_table.add_column("Value", style="white", justify="right", width=15)

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

    # Rates table with color-coded performance indicators
    console.print("[bold cyan]PERFORMANCE RATES[/bold cyan]")
    rates_table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
    rates_table.add_column("Rate", style="dim", width=20)
    rates_table.add_column("Value", justify="right", width=15)

    # Color code subs_per_class (good: ≥2.0, ok: 1.0-1.99, low: <1.0)
    spc = summary["subs_per_class"]
    spc_color = "green" if spc >= 2.0 else "yellow" if spc >= 1.0 else "white"
    rates_table.add_row("Subs per Class", f"[{spc_color}]{spc}[/{spc_color}]")

    # Color code subs_per_roll (good: ≥0.5, ok: 0.3-0.49, low: <0.3)
    spr = summary["subs_per_roll"]
    spr_color = "green" if spr >= 0.5 else "yellow" if spr >= 0.3 else "white"
    rates_table.add_row("Subs per Roll", f"[{spr_color}]{spr}[/{spr_color}]")

    # Color code taps_per_roll (lower is better: green <0.3, yellow 0.3-0.5, red >0.5)
    tpr = summary["taps_per_roll"]
    tpr_color = "green" if tpr < 0.3 else "yellow" if tpr <= 0.5 else "red"
    rates_table.add_row("Taps per Roll", f"[{tpr_color}]{tpr}[/{tpr_color}]")

    # Color code sub_ratio (good: >1.5, ok: 0.8-1.5, low: <0.8)
    ratio = summary["sub_ratio"]
    ratio_color = "green" if ratio > 1.5 else "yellow" if ratio >= 0.8 else "red"
    rates_table.add_row("Sub Ratio (F:A)", f"[{ratio_color}]{ratio}[/{ratio_color}]")

    console.print(rates_table)
    console.print()

    # Breakdown by type
    if report["breakdown_by_type"]:
        console.print("[bold cyan]BREAKDOWN BY CLASS TYPE[/bold cyan]")
        type_table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
        type_table.add_column("Type", style="white", width=15)
        type_table.add_column("Classes", style="cyan", justify="right", width=10)
        type_table.add_column("Hours", style="cyan", justify="right", width=10)
        type_table.add_column("Rolls", style="cyan", justify="right", width=10)

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
        console.print("[bold cyan]BREAKDOWN BY GYM[/bold cyan]")
        gym_table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
        gym_table.add_column("Gym", style="white", width=30)
        gym_table.add_column("Classes", style="cyan", justify="right", width=10)

        for gym, count in sorted(
            report["breakdown_by_gym"].items(), key=lambda x: x[1], reverse=True
        ):
            gym_table.add_row(gym, str(count))

        console.print(gym_table)
        console.print()

    # Weight tracking (if available)
    if report.get("weight_tracking", {}).get("has_data"):
        console.print("[bold cyan]WEIGHT TRACKING[/bold cyan]")
        weight_table = Table(
            show_header=True, header_style="bold cyan", box=box.ROUNDED
        )
        weight_table.add_column("Metric", style="dim", width=20)
        weight_table.add_column("Value", style="white", justify="right", width=15)

        wt = report["weight_tracking"]
        if wt.get("start_weight"):
            weight_table.add_row("Start Weight", f"{wt['start_weight']} kg")
        if wt.get("end_weight"):
            weight_table.add_row("End Weight", f"{wt['end_weight']} kg")
        if wt.get("weight_change") is not None:
            change = wt["weight_change"]
            change_color = "green" if abs(change) < 1 else "yellow"
            sign = "+" if change > 0 else ""
            weight_table.add_row(
                "Change", f"[{change_color}]{sign}{change} kg[/{change_color}]"
            )
        if wt.get("avg_weight"):
            weight_table.add_row("Average", f"{wt['avg_weight']} kg")

        console.print(weight_table)
        console.print()

    # Readiness summary (if available)
    if report.get("readiness") and len(report["readiness"]) > 0:
        console.print("[bold cyan]READINESS SUMMARY[/bold cyan]")
        readiness_table = Table(
            show_header=True, header_style="bold cyan", box=box.ROUNDED
        )
        readiness_table.add_column("Metric", style="dim", width=20)
        readiness_table.add_column("Average", justify="right", width=15)

        # Calculate averages
        readiness_entries = report["readiness"]
        avg_sleep = sum(r.get("sleep", 0) for r in readiness_entries) / len(
            readiness_entries
        )
        avg_stress = sum(r.get("stress", 0) for r in readiness_entries) / len(
            readiness_entries
        )
        avg_soreness = sum(r.get("soreness", 0) for r in readiness_entries) / len(
            readiness_entries
        )
        avg_energy = sum(r.get("energy", 0) for r in readiness_entries) / len(
            readiness_entries
        )
        avg_score = sum(r.get("composite_score", 0) for r in readiness_entries) / len(
            readiness_entries
        )

        # Color code composite score (good: ≥16, ok: 12-15, low: <12)
        score_color = (
            "green" if avg_score >= 16 else "yellow" if avg_score >= 12 else "red"
        )

        readiness_table.add_row("Sleep", f"{avg_sleep:.1f}/5")
        readiness_table.add_row("Stress", f"{avg_stress:.1f}/5")
        readiness_table.add_row("Soreness", f"{avg_soreness:.1f}/5")
        readiness_table.add_row("Energy", f"{avg_energy:.1f}/5")
        readiness_table.add_row(
            "Composite Score", f"[{score_color}]{avg_score:.1f}/20[/{score_color}]"
        )
        readiness_table.add_row("Check-ins", str(len(readiness_entries)))

        console.print(readiness_table)


def _export_csv(service: ReportService, report: dict, filename: str):
    """Export report data to CSV."""
    output_path = Path(filename)
    service.export_to_csv(report["sessions"], str(output_path))
    prompts.print_success(f"Report exported to {output_path}")
