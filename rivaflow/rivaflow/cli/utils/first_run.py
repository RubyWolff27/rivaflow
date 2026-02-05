"""First-run experience for new RivaFlow users."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from rivaflow.cli.utils.logo import LOGO, TAGLINE

console = Console()

# Marker file to track if user has seen welcome message
WELCOME_MARKER = Path.home() / ".rivaflow" / ".welcomed"


def is_first_run() -> bool:
    """Check if this is the user's first time running RivaFlow CLI."""
    return not WELCOME_MARKER.exists()


def mark_welcomed() -> None:
    """Mark that user has seen the welcome message."""
    WELCOME_MARKER.parent.mkdir(parents=True, exist_ok=True)
    WELCOME_MARKER.touch()


def show_welcome_message() -> None:
    """Display welcome message and quick start guide for new users."""
    console.clear()

    # ASCII art logo
    console.print(f"[bold cyan]{LOGO}[/bold cyan]")
    console.print(f"[dim]{TAGLINE}[/dim]")
    console.print()

    console.print(
        Panel(
            "[bold]Welcome to RivaFlow! 🥋[/bold]\n\n[dim]Your Training OS for the Mat[/dim]",
            border_style="cyan",
            padding=(1, 2),
            title="[bold]First Time Setup[/bold]",
        )
    )

    console.print()

    # What is RivaFlow?
    console.print("[bold cyan]What is RivaFlow?[/bold cyan]")
    console.print("  • Track your BJJ/Grappling training sessions")
    console.print("  • Monitor your readiness and recovery")
    console.print("  • View analytics and progress over time")
    console.print("  • Build training streaks and hit milestones")
    console.print()

    # Getting Started
    console.print("[bold cyan]Getting Started[/bold cyan]")
    console.print("  1. [bold]Log in or create an account[/bold]")
    console.print("     [dim]rivaflow auth register[/dim]  (create new account)")
    console.print("     [dim]rivaflow auth login[/dim]     (existing account)")
    console.print()
    console.print("  2. [bold]Log your first training session[/bold]")
    console.print("     [dim]rivaflow log[/dim]")
    console.print()
    console.print("  3. [bold]Check your progress[/bold]")
    console.print("     [dim]rivaflow report week[/dim]    (weekly summary)")
    console.print("     [dim]rivaflow streak[/dim]         (current streaks)")
    console.print("     [dim]rivaflow dashboard[/dim]      (today's overview)")
    console.print()

    # Common Commands
    console.print("[bold cyan]Common Commands[/bold cyan]")
    commands = [
        ("rivaflow log", "Log a training session"),
        ("rivaflow readiness", "Check in with your readiness"),
        ("rivaflow rest", "Log a rest/recovery day"),
        ("rivaflow report week", "View weekly training summary"),
        ("rivaflow streak", "View your training streaks"),
        ("rivaflow --help", "See all available commands"),
    ]

    for cmd, desc in commands:
        console.print(f"  [cyan]{cmd:25}[/cyan] {desc}")

    console.print()

    # Tips
    console.print("[bold cyan]💡 Tips[/bold cyan]")
    console.print("  • Use the web app for a richer experience (if available)")
    console.print("  • Log sessions consistently to build streaks")
    console.print("  • Track readiness to monitor recovery")
    console.print("  • Use [cyan]rivaflow <command> --help[/cyan] for detailed options")
    console.print()

    # Prompt to continue
    if Confirm.ask("[bold]Ready to start?[/bold]", default=True):
        console.print()
        console.print("[green]Great! Let's get started.[/green]")
        console.print()
        console.print(
            "[dim]Hint: Try [cyan]rivaflow auth register[/cyan] to create your account[/dim]"
        )
        console.print()

    mark_welcomed()


def show_quick_start_guide() -> None:
    """Display a condensed quick start guide."""
    console.print()
    console.print("[bold cyan]Quick Start Guide[/bold cyan]")
    console.print()
    console.print("  1. [bold]Register/Login[/bold]")
    console.print("     [dim]rivaflow auth register[/dim]")
    console.print()
    console.print("  2. [bold]Log Your First Session[/bold]")
    console.print("     [dim]rivaflow log[/dim]")
    console.print()
    console.print("  3. [bold]View Your Progress[/bold]")
    console.print("     [dim]rivaflow report week[/dim]")
    console.print()
    console.print("  Type [cyan]rivaflow --help[/cyan] to see all commands")
    console.print()


def maybe_show_welcome() -> None:
    """Show welcome message if this is the user's first run."""
    if is_first_run():
        show_welcome_message()


def reset_welcome() -> None:
    """Reset the welcome marker (for testing)."""
    if WELCOME_MARKER.exists():
        WELCOME_MARKER.unlink()
