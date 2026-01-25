"""Main CLI application using Typer."""
import typer
from typing import Optional
from datetime import date, datetime

from rivaflow.cli.commands import (
    log,
    readiness,
    report,
    suggest,
    video,
    technique,
    dashboard,
    rest,
    streak,
    tomorrow,
    progress,
)

app = typer.Typer(
    name="rivaflow",
    help="Training OS for the mat — Train with intent. Flow to mastery.",
    add_completion=False,
    invoke_without_command=True,  # Allow default command
)

# Register subcommands
app.add_typer(log.app, name="log")
app.add_typer(readiness.app, name="readiness")
app.add_typer(report.app, name="report")
app.add_typer(suggest.app, name="suggest")
app.add_typer(video.app, name="video")
app.add_typer(technique.app, name="technique")

# Engagement commands (v0.2)
app.add_typer(dashboard.app, name="dashboard")
app.add_typer(rest.app, name="rest")
app.add_typer(streak.app, name="streak")
app.add_typer(tomorrow.app, name="tomorrow")
app.add_typer(progress.app, name="progress")


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    """
    RivaFlow: Local-first training tracker for BJJ and grappling.

    Run without arguments to see today's dashboard.
    """
    if ctx.invoked_subcommand is None:
        # No subcommand = show dashboard
        dashboard.dashboard()


@app.command()
def init():
    """Initialize the RivaFlow database."""
    from rivaflow.db.database import init_db

    init_db()
    typer.echo("✓ Database initialized at ~/.rivaflow/rivaflow.db")


@app.command()
def stats():
    """Show quick lifetime statistics."""
    from rich.console import Console
    from rich.table import Table
    from rivaflow.db.repositories import SessionRepository, ReadinessRepository, TechniqueRepository, VideoRepository

    console = Console()

    session_repo = SessionRepository()
    readiness_repo = ReadinessRepository()
    technique_repo = TechniqueRepository()
    video_repo = VideoRepository()

    # Get all sessions
    all_sessions = session_repo.get_recent(limit=99999)  # Get all

    # Calculate stats
    total_classes = len(all_sessions)
    total_rolls = sum(s["rolls"] for s in all_sessions)
    total_mins = sum(s["duration_mins"] for s in all_sessions)
    total_hours = round(total_mins / 60, 1)

    # Get counts
    readiness_count = len(readiness_repo.get_by_date_range(
        date(2000, 1, 1), date.today()
    ))
    technique_count = len(technique_repo.list_all())
    video_count = len(video_repo.list_all())

    # Display
    console.print("[bold]RivaFlow Lifetime Stats[/bold]\n")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Total Sessions", str(total_classes))
    table.add_row("Total Hours", str(total_hours))
    table.add_row("Total Rolls", str(total_rolls))
    table.add_row("Readiness Entries", str(readiness_count))
    table.add_row("Techniques Tracked", str(technique_count))
    table.add_row("Videos Saved", str(video_count))

    console.print(table)


@app.command()
def export():
    """Export all data as JSON."""
    import json
    from pathlib import Path
    from rich.console import Console
    from rivaflow.db.repositories import SessionRepository, ReadinessRepository, TechniqueRepository, VideoRepository
    from rivaflow.config import DB_PATH

    console = Console()

    session_repo = SessionRepository()
    readiness_repo = ReadinessRepository()
    technique_repo = TechniqueRepository()
    video_repo = VideoRepository()

    # Collect all data
    data = {
        "exported_at": datetime.now().isoformat(),
        "database_path": str(DB_PATH),
        "sessions": session_repo.get_recent(limit=99999),  # All sessions
        "readiness": readiness_repo.get_by_date_range(date(2000, 1, 1), date.today()),
        "techniques": technique_repo.list_all(),
        "videos": video_repo.list_all(),
    }

    # Convert dates to strings for JSON serialization
    def default_serializer(obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    # Write to file
    output_file = Path("rivaflow_export.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=default_serializer)

    console.print(f"[green]✓[/green] Data exported to {output_file}")
    console.print(f"  Sessions: {len(data['sessions'])}")
    console.print(f"  Readiness: {len(data['readiness'])}")
    console.print(f"  Techniques: {len(data['techniques'])}")
    console.print(f"  Videos: {len(data['videos'])}")


if __name__ == "__main__":
    app()
