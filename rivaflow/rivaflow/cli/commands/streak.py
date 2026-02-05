"""Streak display command with visual flair."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from rivaflow.cli.utils.user_context import get_current_user_id
from rivaflow.core.services.streak_service import StreakService

app = typer.Typer(
    help="Streak tracking and display",
    invoke_without_command=True,
)
console = Console()


def get_streak_emoji(streak_days: int) -> str:
    """Get fire emoji based on streak length."""
    if streak_days == 0:
        return "💤"  # Sleeping (no streak)
    elif streak_days < 3:
        return "🔥"  # Starting
    elif streak_days < 7:
        return "🔥🔥"  # Building
    elif streak_days < 30:
        return "🔥🔥🔥"  # Strong
    elif streak_days < 90:
        return "🔥🔥🔥🔥"  # Powerful
    elif streak_days < 365:
        return "🔥🔥🔥🔥🔥"  # Legendary
    else:
        return "🔥🔥🔥🔥🔥✨"  # Mythic


def get_streak_color(streak_days: int) -> str:
    """Get color based on streak length."""
    if streak_days == 0:
        return "dim white"
    elif streak_days < 7:
        return "yellow"
    elif streak_days < 30:
        return "bold yellow"
    elif streak_days < 90:
        return "orange1"
    elif streak_days < 365:
        return "red"
    else:
        return "bold magenta"


def get_streak_title(streak_days: int, streak_type: str = "streak") -> str:
    """Get motivational title based on streak length."""
    if streak_days == 0:
        return f"No {streak_type} yet"
    elif streak_days < 3:
        return f"Starting {streak_type}"
    elif streak_days < 7:
        return "Building momentum"
    elif streak_days < 30:
        return "On fire!"
    elif streak_days < 90:
        return "Unstoppable!"
    elif streak_days < 365:
        return "Legendary!"
    else:
        return "🏆 Hall of Fame 🏆"


def render_progress_bar(current: int, milestones: list[int], width: int = 30) -> str:
    """Render a colorful progress bar with gradient effect."""
    # Find the appropriate scale
    max_milestone = max(milestones)

    if current >= max_milestone:
        # Past all milestones - show full bar with celebration
        return "▓" * width + " 🎉"

    # Find next milestone
    next_milestone = None
    for milestone in sorted(milestones):
        if current < milestone:
            next_milestone = milestone
            break

    if next_milestone is None:
        return "▓" * width + " 🎉"

    # Calculate progress
    percentage = current / next_milestone
    filled = int(percentage * width)

    # Use gradient characters for visual interest
    filled_char = "▓"  # Dark shade
    empty_char = "░"  # Light shade
    progress_tip = "▒" if filled < width else ""  # Medium shade at tip

    bar = filled_char * filled
    if filled < width and filled > 0:
        bar = bar[:-1] + progress_tip

    return bar + empty_char * (width - filled)


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


@app.callback(invoke_without_command=True)
def streak(ctx: typer.Context):
    """
    Display current streaks and personal bests.

    Shows:
    - Check-in streak (daily engagement)
    - Training streak (session days)
    - Readiness streak (readiness logged)
    - Milestone markers (7, 30, 90, 365 days)
    - Personal best records
    """
    if ctx.invoked_subcommand is not None:
        return

    user_id = get_current_user_id()
    streak_service = StreakService()
    streaks = streak_service.get_streak_status(user_id)

    # Header
    header = Panel(
        "[bold yellow]🔥 STREAKS[/bold yellow]",
        border_style="yellow",
        padding=(0, 2),
    )
    console.print(header)
    console.print()

    # Milestones for streaks
    streak_milestones = [7, 30, 90, 365]

    # Check-in streak
    checkin_streak = streaks["checkin"]
    current = checkin_streak["current_streak"]
    longest = checkin_streak["longest_streak"]

    fire_emoji = get_streak_emoji(current)
    streak_color = get_streak_color(current)
    title_text = get_streak_title(current, "check-in")

    console.print(
        f"  {fire_emoji} [bold white]CHECK-IN STREAK[/bold white] [dim]— {title_text}[/dim]"
    )
    bar = render_progress_bar(current, streak_milestones)
    console.print(f"  [{streak_color}]{bar}[/{streak_color}]  [bold]{current} days[/bold]")

    if longest > 0 and checkin_streak.get("last_checkin_date"):
        markers = render_milestone_markers(current, streak_milestones)
        console.print(f"  {markers}")

    if checkin_streak.get("grace_days_used", 0) > 0:
        console.print(f"  [dim]⏳ Grace days used: {checkin_streak['grace_days_used']}[/dim]")

    console.print()

    # Training streak
    training_streak = streaks["training"]
    current_training = training_streak["current_streak"]
    longest_training = training_streak["longest_streak"]

    fire_emoji = get_streak_emoji(current_training)
    streak_color = get_streak_color(current_training)
    title_text = get_streak_title(current_training, "training")

    console.print(
        f"  {fire_emoji} [bold white]TRAINING STREAK[/bold white] [dim]— {title_text}[/dim]"
    )
    bar = render_progress_bar(current_training, streak_milestones)
    console.print(f"  [{streak_color}]{bar}[/{streak_color}]  [bold]{current_training} days[/bold]")

    if longest_training > 0 and training_streak.get("last_checkin_date"):
        markers = render_milestone_markers(current_training, streak_milestones)
        console.print(f"  {markers}")

    console.print()

    # Readiness streak
    readiness_streak = streaks["readiness"]
    current_readiness = readiness_streak["current_streak"]
    longest_readiness = readiness_streak["longest_streak"]

    fire_emoji = get_streak_emoji(current_readiness)
    streak_color = get_streak_color(current_readiness)
    title_text = get_streak_title(current_readiness, "readiness")

    console.print(
        f"  {fire_emoji} [bold white]READINESS STREAK[/bold white] [dim]— {title_text}[/dim]"
    )
    bar = render_progress_bar(current_readiness, streak_milestones)
    console.print(
        f"  [{streak_color}]{bar}[/{streak_color}]  [bold]{current_readiness} days[/bold]"
    )

    if longest_readiness > 0 and readiness_streak.get("last_checkin_date"):
        markers = render_milestone_markers(current_readiness, streak_milestones)
        console.print(f"  {markers}")

    console.print()

    # Milestone celebration
    major_milestones = {365: "1 Year", 730: "2 Years", 1095: "3 Years", 1825: "5 Years"}
    for milestone_days, milestone_name in major_milestones.items():
        if (
            current == milestone_days
            or current_training == milestone_days
            or current_readiness == milestone_days
        ):
            celebration = Panel(
                f"[bold yellow]✨ {milestone_name} Streak! ✨[/bold yellow]\n\n"
                f"[white]Incredible dedication! You're an inspiration to the community.[/white]",
                border_style="yellow",
                padding=(1, 2),
            )
            console.print(celebration)
            console.print()
            break

    # Personal bests with better formatting
    if longest > 0 or longest_training > 0 or longest_readiness > 0:
        console.print("  [bold white]🏆 PERSONAL BESTS[/bold white]")

        best_table = Table(show_header=False, box=None, padding=(0, 2))
        best_table.add_column("Type", style="dim")
        best_table.add_column("Days", style="bold yellow")
        best_table.add_column("Date", style="dim")

        if longest > 0:
            best_date = ""
            if checkin_streak.get("streak_started_date"):
                best_date = checkin_streak["streak_started_date"][:7]
            best_table.add_row("Check-in", f"{longest} days", best_date)

        if longest_training > 0:
            best_date = ""
            if training_streak.get("streak_started_date"):
                best_date = training_streak["streak_started_date"][:7]
            best_table.add_row("Training", f"{longest_training} days", best_date)

        if longest_readiness > 0:
            best_date = ""
            if readiness_streak.get("streak_started_date"):
                best_date = readiness_streak["streak_started_date"][:7]
            best_table.add_row("Readiness", f"{longest_readiness} days", best_date)

        console.print(best_table)
        console.print()

    # At risk warning
    if streaks.get("any_at_risk"):
        console.print("  [bold red]⚠️ CHECK IN TODAY TO KEEP YOUR STREAK![/bold red]")
        console.print()
