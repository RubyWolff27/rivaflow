"""Default dashboard command - rivaflow with no arguments."""
from datetime import date, timedelta
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text

from rivaflow.cli.utils.user_context import get_current_user_id
from rivaflow.db.repositories.checkin_repo import CheckinRepository
from rivaflow.core.services.streak_service import StreakService
from rivaflow.core.services.milestone_service import MilestoneService
from rivaflow.db.database import get_connection
from rivaflow.config import TOMORROW_INTENTIONS

app = typer.Typer(
    help="Dashboard and status overview",
    invoke_without_command=True,
)
console = Console()


def get_greeting() -> str:
    """Get time-appropriate greeting."""
    from datetime import datetime
    hour = datetime.now().hour

    if hour < 12:
        return "Good morning"
    elif hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"


def get_week_summary(user_id: int) -> dict:
    """Get this week's training summary."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    with get_connection() as conn:
        cursor = conn.cursor()

        # Sessions count
        cursor.execute("""
            SELECT COUNT(*) FROM sessions
            WHERE user_id = ? AND session_date >= ?
        """, (user_id, week_start.isoformat(),))
        sessions = cursor.fetchone()[0] or 0

        # Total hours
        cursor.execute("""
            SELECT SUM(duration_mins) FROM sessions
            WHERE user_id = ? AND session_date >= ?
        """, (user_id, week_start.isoformat(),))
        total_mins = cursor.fetchone()[0] or 0
        hours = round(total_mins / 60, 1)

        # Total rolls
        cursor.execute("""
            SELECT SUM(rolls) FROM sessions
            WHERE user_id = ? AND session_date >= ?
        """, (user_id, week_start.isoformat(),))
        rolls = cursor.fetchone()[0] or 0

        # Rest days
        cursor.execute("""
            SELECT COUNT(*) FROM daily_checkins
            WHERE user_id = ? AND check_date >= ? AND checkin_type = 'rest'
        """, (user_id, week_start.isoformat(),))
        rest_days = cursor.fetchone()[0] or 0

    return {
        "sessions": sessions,
        "hours": hours,
        "rolls": rolls,
        "rest_days": rest_days,
    }


@app.callback(invoke_without_command=True)
def dashboard(ctx: typer.Context = None):
    """
    Display today's dashboard with quick actions.
    This is the DEFAULT command when user types just 'rivaflow'.
    """
    if ctx and ctx.invoked_subcommand is not None:
        return

    today = date.today()
    day_name = today.strftime("%a %d %b")

    user_id = get_current_user_id()
    checkin_repo = CheckinRepository()
    streak_service = StreakService()
    milestone_service = MilestoneService()

    # Check if this is a first-time user (no sessions logged yet)
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sessions WHERE user_id = ?", (user_id,))
            session_count = cursor.fetchone()[0] or 0

            if session_count == 0:
                # First-time user - show welcome message
                console.print()
                console.print(Panel(
                    "[bold white]Welcome to RivaFlow! 🥋[/bold white]\n\n"
                    "Train with intent. Flow to mastery.\n\n"
                    "[cyan]Get started:[/cyan]\n"
                    "  • [bold]rivaflow log[/bold]       → Log your first training session\n"
                    "  • [bold]rivaflow readiness[/bold] → Check in your readiness\n"
                    "  • [bold]rivaflow --help[/bold]    → See all commands\n\n"
                    "[dim]Once you log a session, your dashboard will show training stats and streaks.[/dim]",
                    border_style="cyan",
                    padding=(1, 2),
                ))
                console.print()
                return
    except Exception:
        pass  # If check fails, continue with normal dashboard

    # Get today's check-in status and data
    with console.status("[cyan]Loading dashboard...", spinner="dots"):
        today_checkin = checkin_repo.get_checkin(user_id, today)
        has_checked_in = today_checkin is not None

        # Get streak info
        checkin_streak = streak_service.get_streak(user_id, "checkin")

        # Get profile name (if available)
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT first_name FROM profile WHERE user_id = ? LIMIT 1", (user_id,))
                row = cursor.fetchone()
                name = row[0] if row and row[0] else "there"
        except Exception:
            name = "there"

        # Preload week summary and milestone data
        summary = get_week_summary(user_id)
        closest = milestone_service.get_closest_milestone(user_id)

    # Header
    header = Panel(
        f"[bold white]🥋 RIVAFLOW[/bold white]                        [dim]{day_name}[/dim]",
        border_style="bright_white",
        padding=(0, 2),
    )
    console.print(header)
    console.print()

    # Greeting and streak
    greeting_text = Text()
    greeting_text.append(f"  {get_greeting()}, {name}.", style="white")

    if checkin_streak["current_streak"] > 0:
        greeting_text.append("                    ", style="white")
        greeting_text.append("🔥 ", style="bold")
        greeting_text.append(f"Streak: {checkin_streak['current_streak']} days", style="bold yellow")

    console.print(greeting_text)
    console.print()

    # Today's status
    if has_checked_in:
        status_icon = "✅"
        if today_checkin["checkin_type"] == "session":
            status_msg = "Checked in (Training session logged)"
        elif today_checkin["checkin_type"] == "rest":
            rest_type = today_checkin.get("rest_type", "recovery")
            status_msg = f"Checked in (Rest day - {rest_type})"
        else:
            status_msg = "Checked in (Readiness only)"
        status_style = "green"
    else:
        status_icon = "⚠️"
        status_msg = "Not checked in yet"
        status_style = "yellow"

    console.print(f"  [bold]TODAY'S STATUS:[/bold] [{status_style}]{status_icon} {status_msg}[/{status_style}]")
    console.print()

    # Week summary (already loaded)
    console.print(f"  [bold]THIS WEEK:[/bold] {summary['sessions']} sessions │ {summary['hours']} hours │ {summary['rolls']} rolls │ {summary['rest_days']} rest days")
    console.print()

    # Quick actions (if not checked in)
    if not has_checked_in:
        console.print("  [dim]Quick actions:[/dim]")
        console.print("  [cyan]rivaflow log[/cyan]       - Log a training session")
        console.print("  [cyan]rivaflow rest[/cyan]      - Log a rest day")
        console.print("  [cyan]rivaflow readiness[/cyan] - Check in with readiness")
        console.print()

    # Show insight if checked in today
    if has_checked_in and today_checkin.get("insight_shown"):
        import json
        try:
            insight = json.loads(today_checkin["insight_shown"])
            console.print(f"  [bold]{insight.get('icon', '💡')} {insight.get('title', 'INSIGHT').upper()}:[/bold]")
            console.print(f"  [dim]{insight.get('message', '')}[/dim]")
            if insight.get('action'):
                console.print(f"  [dim italic]{insight['action']}[/dim italic]")
            console.print()
        except Exception:
            pass

    # Tomorrow's intention
    if today_checkin and today_checkin.get("tomorrow_intention"):
        intention = today_checkin["tomorrow_intention"]
        intention_label = TOMORROW_INTENTIONS.get(intention, intention)
        console.print(f"  [bold]TOMORROW:[/bold] {intention_label}")
        console.print()

    # Show closest milestone (already loaded)
    if closest and closest["percentage"] >= 70:
        bar_length = 20
        filled = int((closest["percentage"] / 100) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        console.print(f"  [bold]NEXT MILESTONE:[/bold]")
        console.print(f"  {closest['next_label']}")
        console.print(f"  [yellow]{bar}[/yellow] {closest['percentage']}% ({closest['remaining']} to go)")
        console.print()

    # Other commands
    console.print("  [dim]More:[/dim]")
    console.print("  [cyan]rivaflow streak[/cyan]    - View all streaks")
    console.print("  [cyan]rivaflow progress[/cyan]  - Lifetime stats and milestones")
    console.print("  [cyan]rivaflow tomorrow[/cyan]  - Set tomorrow's intention")
    console.print()
