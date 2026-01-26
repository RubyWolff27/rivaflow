"""Rest day logging command."""
from datetime import date
import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from rivaflow.core.services.rest_service import RestService
from rivaflow.core.services.milestone_service import MilestoneService
from rivaflow.config import REST_TYPES, TOMORROW_INTENTIONS, MILESTONE_QUOTES
import random

app = typer.Typer(
    help="Rest day logging",
    invoke_without_command=True,
)
console = Console()


def show_milestone_celebration(milestone: dict):
    """Display milestone celebration."""
    quote, author = random.choice(MILESTONE_QUOTES)

    # Progress bar (full)
    bar = "█" * 30

    celebration = f"""
  [bold yellow]{bar}[/bold yellow]  [bold white]{milestone['milestone_label'].upper()}[/bold white]

  [italic]"{quote}"[/italic]
                                        [dim]— {author}[/dim]

  [bold green]🏆 Achievement unlocked:[/bold green] {milestone['achieved_at'][:10]}
"""

    # Get next milestone
    milestone_service = MilestoneService()
    totals = milestone_service.get_current_totals()
    current = totals.get(milestone['milestone_type'], 0)
    next_ms = milestone_service.milestone_repo.get_next_milestone(milestone['milestone_type'], current)

    if next_ms:
        celebration += f"\n  Next milestone: {next_ms['milestone_label']} ({next_ms['remaining']} to go)"

    panel = Panel(
        celebration,
        title="[bold yellow]🎉 MILESTONE UNLOCKED![/bold yellow]",
        border_style="yellow",
        padding=(1, 2),
    )
    console.print(panel)
    console.print()


@app.callback(invoke_without_command=True)
def rest(
    ctx: typer.Context,
    rest_type: str = typer.Option("recovery", "--type", "-t", help="Type: recovery, life, injury, travel"),
    note: Optional[str] = typer.Option(None, "--note", "-n", help="Optional note"),
    tomorrow: Optional[str] = typer.Option(None, "--tomorrow", help="Tomorrow's intention")
):
    """
    Log a rest day. Quick and simple.

    Examples:
        rivaflow rest                          # Default recovery day
        rivaflow rest --type injury            # Injury rest
        rivaflow rest -t travel -n "In Sydney"
    """
    if ctx.invoked_subcommand is not None:
        return

    # Validate rest_type
    if rest_type not in REST_TYPES:
        console.print(f"[red]Error:[/red] Invalid rest type '{rest_type}'")
        console.print(f"Valid types: {', '.join(REST_TYPES.keys())}")
        raise typer.Exit(1)

    # Log rest day
    rest_service = RestService()
    result = rest_service.log_rest_day(
        rest_type=rest_type,
        note=note,
        tomorrow_intention=tomorrow
    )

    # Header
    header = Panel(
        "[bold green]✅ REST DAY LOGGED[/bold green]",
        border_style="green",
        padding=(0, 2),
    )
    console.print(header)
    console.print()

    # Rest details
    rest_type_label = REST_TYPES.get(rest_type, rest_type)
    console.print(f"  [bold]Type:[/bold] {rest_type_label}")
    if note:
        console.print(f"  [bold]Note:[/bold] \"{note}\"")
    console.print()

    # Streak info
    streak_info = result["streak_info"]
    checkin_streak = streak_info["checkin_streak"]

    streak_text = f"  🔥 [bold yellow]Streak: {checkin_streak['current_streak']} days"

    if streak_info["streak_extended"]:
        streak_text += " (+1)"

    if streak_info["grace_day_used"]:
        streak_text += " [dim](used grace day)[/dim]"

    if streak_info["longest_beaten"]:
        streak_text += " [green]🎉 New personal best![/green]"

    streak_text += "[/bold yellow]"

    console.print(streak_text)
    console.print()

    # Insight
    insight = result["insight"]
    console.print(f"  [bold]{insight.get('icon', '💡')} {insight.get('title', 'INSIGHT').upper()}:[/bold]")
    console.print(f"  [dim]{insight.get('message', '')}[/dim]")
    if insight.get('action'):
        console.print(f"  [dim italic]{insight['action']}[/dim italic]")
    console.print()

    # Celebrate milestones
    if result["milestones"]:
        for milestone in result["milestones"]:
            show_milestone_celebration(milestone)
            # Mark as celebrated
            milestone_service = MilestoneService()
            milestone_service.mark_celebrated(milestone["id"])

    # Tomorrow prompt (if not provided)
    if not tomorrow:
        console.print("  [bold]What's the plan for tomorrow?[/bold]")
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

        intention = intention_map.get(choice, "unsure")

        # Update check-in with tomorrow's intention
        from rivaflow.db.repositories.checkin_repo import CheckinRepository
        checkin_repo = CheckinRepository()
        checkin_repo.update_tomorrow_intention(date.today(), intention)

        intention_label = TOMORROW_INTENTIONS.get(intention, intention)
        console.print()
        console.print(f"  [green]✅ Tomorrow:[/green] {intention_label}")
        console.print()
