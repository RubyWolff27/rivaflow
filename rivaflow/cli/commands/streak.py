"""Streak display command."""
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from rivaflow.core.services.streak_service import StreakService

app = typer.Typer(help="Streak tracking and display")
console = Console()


def render_progress_bar(current: int, milestones: list[int], width: int = 30) -> str:
    """Render a progress bar with milestone markers."""
    # Find the appropriate scale
    max_milestone = max(milestones)

    if current >= max_milestone:
        # Past all milestones - show full bar
        return "█" * width

    # Find next milestone
    next_milestone = None
    for milestone in sorted(milestones):
        if current < milestone:
            next_milestone = milestone
            break

    if next_milestone is None:
        return "█" * width

    # Calculate progress
    percentage = current / next_milestone
    filled = int(percentage * width)

    return "█" * filled + "░" * (width - filled)


def render_milestone_markers(current: int, milestones: list[int]) -> str:
    """Render milestone achievement markers."""
    markers = []

    for i, milestone in enumerate(milestones[:4]):  # Show first 4 milestones
        if current >= milestone:
            icon = "✓"
            style = "green"
        else:
            icon = "···"
            style = "dim"

        # Medal icons
        if i == 0:
            medal = "🥉"
        elif i == 1:
            medal = "🥈"
        elif i == 2:
            medal = "🥇"
        else:
            medal = "💎"

        markers.append(f"[{style}]{medal} {milestone} {icon}[/{style}]")

    return "   ".join(markers)


@app.command()
def streak():
    """
    Display current streaks and personal bests.

    Shows:
    - Check-in streak (daily engagement)
    - Training streak (session days)
    - Readiness streak (readiness logged)
    - Milestone markers (7, 30, 90, 365 days)
    - Personal best records
    """
    streak_service = StreakService()
    streaks = streak_service.get_streak_status()

    # Header
    header = Panel(
        "[bold yellow]🔥 STREAKS[/bold yellow]",
        border_style="yellow",
        padding=(0, 2),
    )
    console.print(header)
    console.print()

    # Milestones for streaks
    STREAK_MILESTONES = [7, 30, 90, 365]

    # Check-in streak
    checkin_streak = streaks["checkin"]
    current = checkin_streak["current_streak"]
    longest = checkin_streak["longest_streak"]

    console.print("  [bold white]CHECK-IN STREAK[/bold white]")
    bar = render_progress_bar(current, STREAK_MILESTONES)
    console.print(f"  [yellow]{bar}[/yellow]  [bold]{current} days[/bold]")

    if longest > 0 and checkin_streak.get("last_checkin_date"):
        markers = render_milestone_markers(current, STREAK_MILESTONES)
        console.print(f"  {markers}")

    if checkin_streak.get("grace_days_used", 0) > 0:
        console.print(f"  [dim]Grace days used: {checkin_streak['grace_days_used']}[/dim]")

    console.print()

    # Training streak
    training_streak = streaks["training"]
    current_training = training_streak["current_streak"]
    longest_training = training_streak["longest_streak"]

    console.print("  [bold white]TRAINING STREAK[/bold white]")
    bar = render_progress_bar(current_training, STREAK_MILESTONES)
    console.print(f"  [yellow]{bar}[/yellow]  [bold]{current_training} days[/bold]")

    if longest_training > 0 and training_streak.get("last_checkin_date"):
        markers = render_milestone_markers(current_training, STREAK_MILESTONES)
        console.print(f"  {markers}")

    console.print()

    # Readiness streak
    readiness_streak = streaks["readiness"]
    current_readiness = readiness_streak["current_streak"]
    longest_readiness = readiness_streak["longest_streak"]

    console.print("  [bold white]READINESS STREAK[/bold white]")
    bar = render_progress_bar(current_readiness, STREAK_MILESTONES)
    console.print(f"  [yellow]{bar}[/yellow]  [bold]{current_readiness} days[/bold]")

    if longest_readiness > 0 and readiness_streak.get("last_checkin_date"):
        markers = render_milestone_markers(current_readiness, STREAK_MILESTONES)
        console.print(f"  {markers}")

    console.print()

    # Personal bests
    if longest > 0 or longest_training > 0 or longest_readiness > 0:
        console.print("  [bold white]PERSONAL BESTS[/bold white]")

        if longest > 0:
            best_date = ""
            if checkin_streak.get("streak_started_date"):
                best_date = f" ({checkin_streak['streak_started_date'][:7]})"
            console.print(f"  └─ Longest check-in streak: [bold yellow]{longest} days[/bold yellow]{best_date}")

        if longest_training > 0:
            best_date = ""
            if training_streak.get("streak_started_date"):
                best_date = f" ({training_streak['streak_started_date'][:7]})"
            console.print(f"  └─ Longest training streak: [bold yellow]{longest_training} days[/bold yellow]{best_date}")

        if longest_readiness > 0:
            best_date = ""
            if readiness_streak.get("streak_started_date"):
                best_date = f" ({readiness_streak['streak_started_date'][:7]})"
            console.print(f"  └─ Longest readiness streak: [bold yellow]{longest_readiness} days[/bold yellow]{best_date}")

        console.print()

    # At risk warning
    if streaks.get("any_at_risk"):
        console.print("  [bold red]⚠️ CHECK IN TODAY TO KEEP YOUR STREAK![/bold red]")
        console.print()
