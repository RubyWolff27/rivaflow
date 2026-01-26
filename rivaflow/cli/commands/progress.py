"""Progress and milestones command."""
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from rivaflow.core.services.milestone_service import MilestoneService
from rivaflow.db.database import get_connection

app = typer.Typer(
    help="Lifetime stats and milestone progress",
    invoke_without_command=True,
)
console = Console()


def get_lifetime_stats() -> dict:
    """Calculate all lifetime statistics."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Hours
        cursor.execute("SELECT SUM(duration_mins) FROM sessions")
        total_mins = cursor.fetchone()[0] or 0
        hours = round(total_mins / 60, 1)

        # Sessions
        cursor.execute("SELECT COUNT(*) FROM sessions")
        sessions = cursor.fetchone()[0] or 0

        # Rolls
        cursor.execute("SELECT SUM(rolls) FROM sessions")
        rolls = cursor.fetchone()[0] or 0

        # Submissions for
        cursor.execute("SELECT SUM(submissions_for) FROM sessions")
        subs_for = cursor.fetchone()[0] or 0

        # Submissions against
        cursor.execute("SELECT SUM(submissions_against) FROM sessions")
        subs_against = cursor.fetchone()[0] or 0

        # Sub ratio
        sub_ratio = round(subs_for / subs_against, 2) if subs_against > 0 else subs_for

        # Partners
        cursor.execute("""
            SELECT COUNT(DISTINCT partner_id)
            FROM session_rolls
            WHERE partner_id IS NOT NULL
        """)
        partners = cursor.fetchone()[0] or 0

        # Techniques
        cursor.execute("""
            SELECT COUNT(DISTINCT movement_id)
            FROM session_techniques
        """)
        techniques = cursor.fetchone()[0] or 0

    return {
        "hours": hours,
        "sessions": sessions,
        "rolls": rolls,
        "partners": partners,
        "techniques": techniques,
        "subs_for": subs_for,
        "subs_against": subs_against,
        "sub_ratio": sub_ratio,
    }


@app.callback(invoke_without_command=True)
def progress(ctx: typer.Context):
    """
    Display lifetime stats and milestone progress.

    Shows:
    - Total hours, sessions, rolls, partners, techniques
    - Submission statistics and ratio
    - Achieved milestones
    - Progress toward next milestones
    - Closest upcoming milestone
    """
    if ctx.invoked_subcommand is not None:
        return

    milestone_service = MilestoneService()

    # Header
    header = Panel(
        "[bold cyan]📊 LIFETIME PROGRESS[/bold cyan]",
        border_style="cyan",
        padding=(0, 2),
    )
    console.print(header)
    console.print()

    # Lifetime stats table
    stats = get_lifetime_stats()

    table = Table(title="TOTALS", border_style="bright_black", show_header=True)
    table.add_column("Metric", style="white", width=20)
    table.add_column("Value", style="bold yellow", justify="right", width=12)

    table.add_row("Hours on Mat", str(stats["hours"]))
    table.add_row("Sessions", str(stats["sessions"]))
    table.add_row("Rolls", str(stats["rolls"]))
    table.add_row("Partners", str(stats["partners"]))
    table.add_row("Techniques", str(stats["techniques"]))
    table.add_row("Submissions For", str(stats["subs_for"]))
    table.add_row("Submissions Against", str(stats["subs_against"]))
    table.add_row("Sub Ratio", str(stats["sub_ratio"]))

    console.print(table)
    console.print()

    # Milestones section
    console.print("  [bold white]MILESTONES[/bold white]")
    console.print()

    # Get achieved milestones
    achieved = milestone_service.get_all_achieved()

    # Get progress to next
    progress_list = milestone_service.get_progress_to_next()

    # Group by type
    milestone_types = ["hours", "sessions", "streak", "rolls", "partners", "techniques"]

    for mtype in milestone_types:
        # Get highest achieved for this type
        type_achieved = [m for m in achieved if m["milestone_type"] == mtype]
        type_progress = [p for p in progress_list if p["type"] == mtype]

        if type_achieved or type_progress:
            # Show highest achieved
            if type_achieved:
                highest = max(type_achieved, key=lambda x: x["milestone_value"])
                console.print(f"  [green]✅[/green] {highest['milestone_label']}")

            # Show progress to next
            if type_progress:
                prog = type_progress[0]
                bar_length = 10
                filled = int((prog["percentage"] / 100) * bar_length)
                bar = "█" * filled + "░" * (bar_length - filled)

                remaining_text = f"({prog['remaining']} to go)"
                console.print(f"  [dim]⬜ {prog['next_label']} [yellow]{bar}[/yellow] {prog['percentage']}% {remaining_text}[/dim]")

    console.print()

    # Next milestone highlight
    closest = milestone_service.get_closest_milestone()
    if closest:
        unit_map = {
            "hours": "hours",
            "sessions": "sessions",
            "rolls": "rolls",
            "partners": "partners",
            "techniques": "techniques",
            "streak": "days",
        }
        unit = unit_map.get(closest["type"], closest["type"])

        console.print(f"  [bold yellow]🎯 NEXT MILESTONE:[/bold yellow] {closest['next_label']}")
        console.print(f"  [dim]{closest['remaining']} {unit} away ({closest['percentage']}% complete)[/dim]")
        console.print()


@app.command()
def milestones():
    """Show only milestone achievements (compact view)."""
    milestone_service = MilestoneService()
    achieved = milestone_service.get_all_achieved()

    if not achieved:
        console.print("  [dim]No milestones achieved yet. Keep training![/dim]")
        console.print()
        return

    # Header
    header = Panel(
        "[bold yellow]🏆 ACHIEVEMENTS[/bold yellow]",
        border_style="yellow",
        padding=(0, 2),
    )
    console.print(header)
    console.print()

    # Group by type
    by_type = {}
    for milestone in achieved:
        mtype = milestone["milestone_type"]
        if mtype not in by_type:
            by_type[mtype] = []
        by_type[mtype].append(milestone)

    for mtype, milestones in by_type.items():
        console.print(f"  [bold white]{mtype.upper()}:[/bold white]")
        for milestone in sorted(milestones, key=lambda x: x["milestone_value"]):
            date_str = milestone["achieved_at"][:10]
            console.print(f"  └─ [yellow]{milestone['milestone_label']}[/yellow] [dim]({date_str})[/dim]")
        console.print()
