"""Onboarding setup wizard for new users."""
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich import box
from datetime import date

from rivaflow.cli.utils.user_context import get_current_user_id
from rivaflow.cli import prompts
from rivaflow.cli.utils.logo import LOGO, TAGLINE
from rivaflow.db.database import get_connection, convert_query
from rivaflow.config import ALL_CLASS_TYPES

app = typer.Typer(help="First-time setup wizard")
console = Console()


@app.callback(invoke_without_command=True)
def setup(ctx: typer.Context):
    """
    Interactive onboarding wizard for new RivaFlow users.

    Walks through:
    - Profile setup (name, belt rank, home gym)
    - Weekly training goals
    - Optional first session logging
    - Dashboard walkthrough

    \b
    Examples:
      $ rivaflow setup
      $ rivaflow setup --skip  # Skip wizard, use defaults
    """
    if ctx.invoked_subcommand is not None:
        return

    user_id = get_current_user_id()

    # Check if user has already completed setup
    if _is_setup_complete(user_id):
        console.print("\n[yellow]⚠️  You've already completed setup.[/yellow]")
        if not Confirm.ask("\nWould you like to update your profile?"):
            console.print("\n[dim]Run 'rivaflow profile' to update your settings.[/dim]")
            return

    # Welcome screen
    _show_welcome()

    # Step 1: Profile setup
    console.print("\n[bold cyan]STEP 1: Your Profile[/bold cyan]")
    console.print("[dim]Tell us about yourself[/dim]\n")

    profile_data = _collect_profile_data(user_id)
    _save_profile(user_id, profile_data)

    console.print("\n[green]✓[/green] Profile saved!")

    # Step 2: Weekly goals
    console.print("\n[bold cyan]STEP 2: Training Goals[/bold cyan]")
    console.print("[dim]Set your weekly targets to stay on track[/dim]\n")

    goals_data = _collect_goals_data()
    _save_goals(user_id, goals_data)

    console.print("\n[green]✓[/green] Goals set!")

    # Step 3: Optional first session
    console.print("\n[bold cyan]STEP 3: Log Your First Session (Optional)[/bold cyan]")
    console.print("[dim]Let's capture your most recent training[/dim]\n")

    if Confirm.ask("Would you like to log a recent session now?", default=True):
        _log_first_session(user_id)
        console.print("\n[green]✓[/green] First session logged!")
    else:
        console.print("\n[dim]No problem! You can log sessions anytime with:[/dim]")
        console.print("[cyan]rivaflow log[/cyan]")

    # Step 4: Quick tour
    _show_quick_tour()

    # Mark setup as complete
    _mark_setup_complete(user_id)

    # Show dashboard
    console.print("\n[bold yellow]🎉 Setup Complete! Here's your dashboard:[/bold yellow]\n")

    from rivaflow.cli.commands.dashboard import dashboard
    dashboard()


def _show_welcome():
    """Display welcome screen."""
    console.print()
    console.print(f"[bold cyan]{LOGO}[/bold cyan]")
    console.print(f"[dim]{TAGLINE}[/dim]")
    console.print()

    welcome_panel = Panel(
        "[bold white]Welcome to RivaFlow! 🥋[/bold white]\n\n"
        "Let's get you set up in just a few steps.\n\n"
        "[cyan]This will take about 2-3 minutes.[/cyan]",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(welcome_panel)


def _is_setup_complete(user_id: int) -> bool:
    """Check if user has completed setup."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Check if profile exists with basic info
        cursor.execute(
            convert_query("SELECT first_name, belt_rank FROM profile WHERE user_id = ? LIMIT 1"),
            (user_id,)
        )
        profile = cursor.fetchone()

        if not profile or not profile[0] or not profile[1]:
            return False

        # Check if has logged at least one session
        cursor.execute(
            convert_query("SELECT COUNT(*) FROM sessions WHERE user_id = ?"),
            (user_id,)
        )
        session_count = cursor.fetchone()[0]

        return session_count > 0


def _collect_profile_data(user_id: int) -> dict:
    """Collect profile information from user."""
    # Get existing email from user account
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query("SELECT email, first_name, last_name FROM users WHERE id = ? LIMIT 1"),
            (user_id,)
        )
        user = cursor.fetchone()
        email = user[0] if user else ""
        existing_first = user[1] if user else ""
        existing_last = user[2] if user else ""

    # First name
    first_name = Prompt.ask(
        "  [bold]First Name[/bold]",
        default=existing_first if existing_first else None
    )

    # Last name
    last_name = Prompt.ask(
        "  [bold]Last Name[/bold]",
        default=existing_last if existing_last else None
    )

    # Belt rank
    console.print("\n  [bold]Current Belt Rank[/bold]")
    console.print("  [dim]1) White  2) Blue  3) Purple  4) Brown  5) Black[/dim]")
    belt_choice = Prompt.ask(
        "  Select",
        choices=["1", "2", "3", "4", "5"],
        default="1"
    )

    belt_map = {"1": "white", "2": "blue", "3": "purple", "4": "brown", "5": "black"}
    belt_rank = belt_map[belt_choice]

    # Stripes
    belt_stripes = IntPrompt.ask(
        "  [bold]Stripes on current belt[/bold]",
        default=0
    )
    if belt_stripes < 0 or belt_stripes > 4:
        belt_stripes = 0

    # Home gym
    gym_name = Prompt.ask(
        "\n  [bold]Home Gym / Academy[/bold]",
        default="My Academy"
    )

    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "belt_rank": belt_rank,
        "belt_stripes": belt_stripes,
        "gym_name": gym_name,
    }


def _save_profile(user_id: int, data: dict):
    """Save profile data to database."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Update user table
        cursor.execute(
            convert_query("""
                UPDATE users
                SET first_name = ?, last_name = ?
                WHERE id = ?
            """),
            (data["first_name"], data["last_name"], user_id)
        )

        # Check if profile exists
        cursor.execute(
            convert_query("SELECT id FROM profile WHERE user_id = ? LIMIT 1"),
            (user_id,)
        )
        profile_exists = cursor.fetchone()

        if profile_exists:
            # Update existing profile
            cursor.execute(
                convert_query("""
                    UPDATE profile
                    SET first_name = ?, last_name = ?, email = ?,
                        belt_rank = ?, belt_stripes = ?, gym_name = ?
                    WHERE user_id = ?
                """),
                (
                    data["first_name"],
                    data["last_name"],
                    data["email"],
                    data["belt_rank"],
                    data["belt_stripes"],
                    data["gym_name"],
                    user_id,
                )
            )
        else:
            # Create new profile
            cursor.execute(
                convert_query("""
                    INSERT INTO profile (user_id, first_name, last_name, email, belt_rank, belt_stripes, gym_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """),
                (
                    user_id,
                    data["first_name"],
                    data["last_name"],
                    data["email"],
                    data["belt_rank"],
                    data["belt_stripes"],
                    data["gym_name"],
                )
            )


def _collect_goals_data() -> dict:
    """Collect weekly training goals."""
    console.print("  [dim]How many times per week do you want to train?[/dim]\n")

    bjj_goal = IntPrompt.ask(
        "  [bold]🥋 BJJ/Grappling sessions per week[/bold]",
        default=3
    )

    sc_goal = IntPrompt.ask(
        "  [bold]🏋️  S&C sessions per week[/bold]",
        default=2
    )

    mobility_goal = IntPrompt.ask(
        "  [bold]🧘 Mobility/Recovery minutes per week[/bold]",
        default=60
    )

    return {
        "bjj_sessions_goal": max(0, bjj_goal),
        "sc_sessions_goal": max(0, sc_goal),
        "mobility_mins_goal": max(0, mobility_goal),
    }


def _save_goals(user_id: int, data: dict):
    """Save weekly goals to profile."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            convert_query("""
                UPDATE profile
                SET weekly_bjj_goal = ?, weekly_sc_goal = ?, weekly_mobility_goal = ?
                WHERE user_id = ?
            """),
            (
                data["bjj_sessions_goal"],
                data["sc_sessions_goal"],
                data["mobility_mins_goal"],
                user_id,
            )
        )


def _log_first_session(user_id: int):
    """Quick session logging."""
    from rivaflow.db.repositories.session_repo import SessionRepository

    console.print()

    # Session date
    session_date_str = Prompt.ask(
        "  [bold]When did you train?[/bold] (YYYY-MM-DD or 'today')",
        default="today"
    )

    if session_date_str.lower() == "today":
        session_date = date.today()
    else:
        try:
            session_date = date.fromisoformat(session_date_str)
        except ValueError:
            prompts.print_error("Invalid date format. Using today.")
            session_date = date.today()

    # Class type
    console.print("\n  [bold]Class Type[/bold]")
    console.print("  [dim]1) Gi  2) No-Gi  3) Wrestling  4) S&C  5) Mobility[/dim]")
    class_choice = Prompt.ask("  Select", choices=["1", "2", "3", "4", "5"], default="1")

    class_map = {
        "1": "gi",
        "2": "no-gi",
        "3": "wrestling",
        "4": "s&c",
        "5": "mobility"
    }
    class_type = class_map[class_choice]

    # Duration
    duration = IntPrompt.ask("\n  [bold]Duration (minutes)[/bold]", default=90)

    # Intensity
    intensity = IntPrompt.ask(
        "  [bold]Intensity (1-5)[/bold]",
        default=4
    )
    intensity = max(1, min(5, intensity))

    # Rolls (if applicable)
    rolls = 0
    if class_type in ["gi", "no-gi", "wrestling", "open-mat"]:
        rolls = IntPrompt.ask("  [bold]Number of rolls[/bold]", default=5)

    # Get gym from profile
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query("SELECT gym_name FROM profile WHERE user_id = ? LIMIT 1"),
            (user_id,)
        )
        result = cursor.fetchone()
        gym_name = result[0] if result and result[0] else "My Academy"

    # Create session
    repo = SessionRepository()
    session_id = repo.create(
        user_id=user_id,
        session_date=session_date,
        class_type=class_type,
        gym_name=gym_name,
        duration_mins=duration,
        intensity=intensity,
        rolls=rolls,
        submissions_for=0,
        submissions_against=0,
    )

    console.print(f"\n[green]✓[/green] Session #{session_id} created!")


def _mark_setup_complete(user_id: int):
    """Mark setup as complete in profile."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query("UPDATE profile SET setup_completed = 1 WHERE user_id = ?"),
            (user_id,)
        )


def _show_quick_tour():
    """Show quick tour of commands."""
    console.print("\n")

    tour_panel = Panel(
        "[bold cyan]🚀 Quick Start Guide[/bold cyan]\n\n"
        "[bold]Common Commands:[/bold]\n"
        "  • [cyan]rivaflow log[/cyan]       - Log a training session\n"
        "  • [cyan]rivaflow readiness[/cyan] - Check in your daily readiness\n"
        "  • [cyan]rivaflow streak[/cyan]    - View your training streaks\n"
        "  • [cyan]rivaflow progress[/cyan]  - See lifetime stats\n"
        "  • [cyan]rivaflow report week[/cyan] - Weekly training summary\n\n"
        "[bold]Tips:[/bold]\n"
        "  • Log sessions consistently to build streaks 🔥\n"
        "  • Check in daily with readiness to track recovery\n"
        "  • Use [cyan]rivaflow --help[/cyan] to see all commands\n\n"
        "[dim]Your dashboard will show after this...[/dim]",
        border_style="cyan",
        padding=(1, 2),
    )

    console.print(tour_panel)
    console.print()
    Prompt.ask("[bold]Press Enter to continue[/bold]", default="", show_default=False)
