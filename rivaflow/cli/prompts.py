"""Interactive prompts using Rich."""
from typing import Optional, Callable
from rich.console import Console
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.table import Table
from rich.panel import Panel

console = Console()


def prompt_text(
    message: str,
    default: Optional[str] = None,
    choices: Optional[list[str]] = None,
    autocomplete: Optional[list[str]] = None,
) -> str:
    """Prompt for text input with optional autocomplete."""
    if autocomplete and len(autocomplete) > 0:
        # Show autocomplete hints if available
        console.print(f"[dim]Recent: {', '.join(autocomplete[:5])}[/dim]")

    return Prompt.ask(message, default=default, choices=choices)


def prompt_int(
    message: str, default: Optional[int] = None, min_val: int = 0, max_val: int = 999
) -> int:
    """Prompt for integer input."""
    while True:
        value = IntPrompt.ask(message, default=default)
        if min_val <= value <= max_val:
            return value
        console.print(f"[red]Value must be between {min_val} and {max_val}[/red]")


def prompt_list(
    message: str,
    delimiter: str = ",",
    autocomplete: Optional[list[str]] = None,
    optional: bool = True,
) -> Optional[list[str]]:
    """Prompt for comma-separated list input."""
    if autocomplete and len(autocomplete) > 0:
        console.print(f"[dim]Known: {', '.join(autocomplete[:8])}[/dim]")

    result = Prompt.ask(message, default="" if optional else None)
    if not result:
        return None

    # Split and clean
    items = [item.strip() for item in result.split(delimiter) if item.strip()]
    return items if items else None


def prompt_choice(message: str, choices: list[str], default: Optional[str] = None) -> str:
    """Prompt for selection from a list of choices."""
    # Display choices in a more readable format
    for i, choice in enumerate(choices, 1):
        console.print(f"  {i}. {choice}")

    return Prompt.ask(message, choices=choices, default=default)


def confirm(message: str, default: bool = False) -> bool:
    """Prompt for yes/no confirmation."""
    return Confirm.ask(message, default=default)


def display_recall_card(technique_name: str, videos: list[dict]) -> None:
    """Display a recall card for a technique with linked videos."""
    if not videos:
        return

    for video in videos:
        lines = [f"[bold cyan]📹 RECALL: {technique_name}[/bold cyan]"]

        if video.get("title"):
            lines.append(f"[white]{video['title']}[/white]")

        if video.get("timestamps"):
            for ts in video["timestamps"]:
                lines.append(f"  → {ts['time']} - {ts['label']}")

        panel = Panel(
            "\n".join(lines), border_style="cyan", padding=(0, 1), expand=False
        )
        console.print(panel)


def display_summary_table(data: dict) -> None:
    """Display a summary table."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="dim")
    table.add_column("Value", style="white")

    for key, value in data.items():
        table.add_row(key, str(value))

    console.print(table)


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]✗[/red] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[blue]ℹ[/blue] {message}")
