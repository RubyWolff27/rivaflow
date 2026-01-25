"""Main CLI application using Typer."""
import typer
from typing import Optional

from rivaflow.cli.commands import log, readiness, report, suggest, video

app = typer.Typer(
    name="rivaflow",
    help="Training OS for the mat — Train with intent. Flow to mastery.",
    add_completion=False,
)

# Register subcommands
app.add_typer(log.app, name="log")
app.add_typer(readiness.app, name="readiness")
app.add_typer(report.app, name="report")
app.add_typer(suggest.app, name="suggest")
app.add_typer(video.app, name="video")


@app.callback()
def callback():
    """RivaFlow: Local-first training tracker for BJJ and grappling."""
    pass


@app.command()
def init():
    """Initialize the RivaFlow database."""
    from rivaflow.db.database import init_db

    init_db()
    typer.echo("✓ Database initialized at ~/.rivaflow/rivaflow.db")


@app.command()
def stats():
    """Show quick lifetime statistics."""
    typer.echo("Stats command - coming soon!")


@app.command()
def export():
    """Export all data as JSON."""
    typer.echo("Export command - coming soon!")


if __name__ == "__main__":
    app()
