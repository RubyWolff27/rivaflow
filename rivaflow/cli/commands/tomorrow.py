"""Tomorrow's intention command."""
from datetime import date, timedelta
import typer
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

from rivaflow.db.repositories.checkin_repo import CheckinRepository
from rivaflow.db.database import get_connection
from rivaflow.config import TOMORROW_INTENTIONS

app = typer.Typer(
    help="Set tomorrow's training intention",
    invoke_without_command=True,
)
console = Console()


def get_tip_based_on_recent_sessions() -> Optional[str]:
    """Generate contextual tip based on recent training."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Get last 3 sessions
        cursor.execute("""
            SELECT class_type FROM sessions
            ORDER BY session_date DESC
            LIMIT 3
        """)
        recent_sessions = [row[0] for row in cursor.fetchall()]

        if not recent_sessions:
            return None

        # Check if all recent sessions are same type
        if len(recent_sessions) >= 3:
            if all(ct == "gi" for ct in recent_sessions):
                return "💡 TIP: Last 3 sessions were Gi — consider No-Gi to unload grips"
            elif all(ct == "no-gi" for ct in recent_sessions):
                return "💡 TIP: Last 3 sessions were No-Gi — consider Gi work for grips"

        # Check training intensity
        cursor.execute("""
            SELECT COUNT(*) FROM sessions
            WHERE session_date >= date('now', '-6 days')
        """)
        recent_count = cursor.fetchone()[0] or 0

        if recent_count >= 6:
            return "💡 TIP: You've trained 6 of the last 7 days — recovery is training too"

    return None


@app.callback(invoke_without_command=True)
def tomorrow(
    ctx: typer.Context,
    intention: Optional[str] = typer.Argument(None, help="Intention: train_gi, train_nogi, rest, unsure")
):
    """
    Set or view tomorrow's training intention.

    Examples:
        rivaflow tomorrow              # Interactive selection
        rivaflow tomorrow train_gi     # Direct set
        rivaflow tomorrow rest         # Planning rest

    Helps with planning and accountability.
    """
    if ctx.invoked_subcommand is not None:
        return

    checkin_repo = CheckinRepository()
    today = date.today()
    tomorrow_date = today + timedelta(days=1)

    # Check if today's check-in exists
    today_checkin = checkin_repo.get_checkin(today)

    # If intention provided directly, set it
    if intention:
        if intention not in TOMORROW_INTENTIONS:
            console.print(f"[red]Error:[/red] Invalid intention '{intention}'")
            console.print(f"Valid intentions: {', '.join(TOMORROW_INTENTIONS.keys())}")
            raise typer.Exit(1)

        # Update or create check-in with intention
        if today_checkin:
            checkin_repo.update_tomorrow_intention(today, intention)
        else:
            # Create a check-in with readiness_only if no check-in exists
            checkin_repo.upsert_checkin(
                check_date=today,
                checkin_type="readiness_only",
                tomorrow_intention=intention
            )

        intention_label = TOMORROW_INTENTIONS.get(intention, intention)
        console.print(f"  [green]✅ Tomorrow:[/green] {intention_label}")
        console.print()
        return

    # Interactive mode
    console.print()
    console.print("  [bold white]What's the plan for tomorrow?[/bold white]")
    console.print()
    console.print("  [bold]TRAIN:[/bold]")
    console.print("    [cyan]1[/cyan] 🥋 Gi training")
    console.print("    [cyan]2[/cyan] 🩳 No-Gi training")
    console.print("    [cyan]3[/cyan] 🤼 Wrestling")
    console.print("    [cyan]4[/cyan] 🔓 Open mat")
    console.print("    [cyan]5[/cyan] 🏋️ S&C / Conditioning")
    console.print("    [cyan]6[/cyan] 🧘 Mobility / Yoga")
    console.print()
    console.print("  [bold]REST:[/bold]")
    console.print("    [cyan]7[/cyan] 😴 Rest day")
    console.print("    [cyan]8[/cyan] 🤷 Not sure yet")
    console.print()

    choice = Prompt.ask("  Select", choices=["1", "2", "3", "4", "5", "6", "7", "8"], default="8")

    intention_map = {
        "1": "train_gi",
        "2": "train_nogi",
        "3": "train_wrestling",
        "4": "train_open",
        "5": "train_sc",
        "6": "train_mobility",
        "7": "rest",
        "8": "unsure",
    }

    selected_intention = intention_map.get(choice, "unsure")

    # Update or create check-in
    if today_checkin:
        checkin_repo.update_tomorrow_intention(today, selected_intention)
    else:
        checkin_repo.upsert_checkin(
            check_date=today,
            checkin_type="readiness_only",
            tomorrow_intention=selected_intention
        )

    intention_label = TOMORROW_INTENTIONS.get(selected_intention, selected_intention)

    console.print()
    console.print(f"  [green]✅ Tomorrow:[/green] {intention_label}")
    console.print()

    # Show contextual tip
    tip = get_tip_based_on_recent_sessions()
    if tip:
        console.print(f"  [dim]{tip}[/dim]")
        console.print()


@app.command()
def view():
    """View tomorrow's current intention (if set)."""
    checkin_repo = CheckinRepository()
    today = date.today()

    today_checkin = checkin_repo.get_checkin(today)

    if today_checkin and today_checkin.get("tomorrow_intention"):
        intention = today_checkin["tomorrow_intention"]
        intention_label = TOMORROW_INTENTIONS.get(intention, intention)
        console.print(f"  [bold]Tomorrow's plan:[/bold] {intention_label}")
    else:
        console.print("  [dim]No intention set for tomorrow.[/dim]")
        console.print("  Run [cyan]rivaflow tomorrow[/cyan] to set one.")

    console.print()
