"""Main CLI application using Typer."""
import typer
from typing import Optional
from datetime import date, datetime

from rivaflow.cli.commands import (
    auth,
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
app.add_typer(auth.app, name="auth")
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
    # Show welcome message on first run
    from rivaflow.cli.utils.first_run import maybe_show_welcome
    maybe_show_welcome()

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
def export(
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path (default: rivaflow_export.json)")
):
    """Export all your data as JSON (GDPR-compliant data portability)."""
    import json
    from pathlib import Path
    from rich.console import Console
    from rich.prompt import Confirm
    from rivaflow.cli.utils.user_context import get_current_user_id
    from rivaflow.db.repositories import (
        SessionRepository, ReadinessRepository, TechniqueRepository,
        VideoRepository, GradingRepository, FriendRepository,
        UserRepository, ProfileRepository
    )
    from rivaflow.config import DB_PATH

    console = Console()
    user_id = get_current_user_id()

    console.print("[cyan]Exporting your data...[/cyan]")

    # Initialize repositories
    user_repo = UserRepository()
    profile_repo = ProfileRepository()
    session_repo = SessionRepository()
    readiness_repo = ReadinessRepository()
    technique_repo = TechniqueRepository()
    video_repo = VideoRepository()
    grading_repo = GradingRepository()
    friend_repo = FriendRepository()

    # Get user info
    user = user_repo.get_by_id(user_id)
    profile = profile_repo.get_by_user_id(user_id)

    # Collect all data
    data = {
        "exported_at": datetime.now().isoformat(),
        "export_version": "1.0",
        "user": {
            "id": user_id,
            "email": user.get("email") if user else None,
            "first_name": user.get("first_name") if user else None,
            "last_name": user.get("last_name") if user else None,
            "created_at": user.get("created_at") if user else None,
        },
        "profile": profile,
        "sessions": session_repo.list_by_user(user_id),
        "readiness": readiness_repo.list_by_user(user_id),
        "techniques": technique_repo.list_all(user_id),
        "videos": video_repo.list_all(user_id),
        "gradings": grading_repo.list_all(user_id),
        "friends": friend_repo.list_all(user_id),
    }

    # Convert dates to strings for JSON serialization
    def default_serializer(obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    # Determine output file
    output_file = Path(output) if output else Path(f"rivaflow_export_{user_id}_{date.today()}.json")

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=default_serializer, ensure_ascii=False)

    console.print(f"[green]✓[/green] Data exported successfully to [bold]{output_file}[/bold]")
    console.print()
    console.print("[bold]Export Summary:[/bold]")
    console.print(f"  Sessions: {len(data['sessions'])}")
    console.print(f"  Readiness Entries: {len(data['readiness'])}")
    console.print(f"  Techniques: {len(data['techniques'])}")
    console.print(f"  Videos: {len(data['videos'])}")
    console.print(f"  Gradings: {len(data['gradings'])}")
    console.print(f"  Friends: {len(data['friends'])}")
    console.print()
    console.print("[dim]This file contains all your RivaFlow data in JSON format.[/dim]")
    console.print("[dim]Keep it safe - it includes personal information.[/dim]")


@app.command()
def delete_account(
    confirm: bool = typer.Option(False, "--confirm", help="Confirm account deletion")
):
    """Delete your account and all associated data (GDPR right to erasure)."""
    from rich.console import Console
    from rich.prompt import Confirm
    from rivaflow.cli.utils.user_context import get_current_user_id, CREDENTIALS_FILE
    from rivaflow.db.repositories import UserRepository
    from rivaflow.db.database import get_connection, convert_query

    console = Console()
    user_id = get_current_user_id()

    console.print()
    console.print("[bold red]⚠️  WARNING: Account Deletion[/bold red]")
    console.print()
    console.print("This will [bold]permanently delete[/bold]:")
    console.print("  • Your user account")
    console.print("  • All training sessions")
    console.print("  • All readiness check-ins")
    console.print("  • All techniques and videos")
    console.print("  • All gradings and progression data")
    console.print("  • All friends and relationships")
    console.print("  • Your profile and settings")
    console.print()
    console.print("[bold yellow]This action CANNOT be undone![/bold yellow]")
    console.print()

    # Double confirmation
    if not confirm:
        if not Confirm.ask("[bold]Are you sure you want to delete your account?[/bold]", default=False):
            console.print("[green]Account deletion cancelled.[/green]")
            return

    # Triple confirmation with email
    user_repo = UserRepository()
    user = user_repo.get_by_id(user_id)

    if user:
        console.print()
        console.print(f"Please type your email address ([bold]{user.get('email')}[/bold]) to confirm:")
        from rich.prompt import Prompt
        typed_email = Prompt.ask("Email")

        if typed_email != user.get("email"):
            console.print("[red]Email does not match. Account deletion cancelled.[/red]")
            return

    console.print()
    console.print("[cyan]Deleting account...[/cyan]")

    try:
        # Delete user (CASCADE will delete related data)
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("DELETE FROM users WHERE id = ?"), (user_id,))

        # Remove local credentials
        if CREDENTIALS_FILE.exists():
            CREDENTIALS_FILE.unlink()

        console.print()
        console.print("[green]✓[/green] Account deleted successfully.")
        console.print()
        console.print("[dim]Your account and all associated data have been permanently removed.[/dim]")
        console.print("[dim]Thank you for using RivaFlow. We hope to see you again someday! 🥋[/dim]")
        console.print()

    except Exception as e:
        console.print(f"[red]Error deleting account: {e}[/red]")
        console.print("[yellow]Please contact support if this problem persists.[/yellow]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
