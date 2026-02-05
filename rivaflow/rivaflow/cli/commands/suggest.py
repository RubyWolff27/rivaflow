"""Training suggestion commands."""

import typer
from rich.console import Console
from rich.panel import Panel

from rivaflow.cli.utils.user_context import get_current_user_id
from rivaflow.core.services.suggestion_engine import SuggestionEngine

app = typer.Typer(help="Training suggestions and recommendations")
console = Console()


@app.command()
def suggest(
    explain: bool = typer.Option(
        False, "--explain", "-e", help="Show verbose rule explanations"
    ),
):
    """Get today's training recommendation."""
    user_id = get_current_user_id()
    engine = SuggestionEngine()
    result = engine.get_suggestion(user_id)

    # Header
    header = Panel(
        "[bold cyan]🥋 TODAY'S RECOMMENDATION[/bold cyan]",
        border_style="cyan",
        padding=(0, 2),
    )
    console.print(header)
    console.print()

    # Primary suggestion
    console.print(f"  [bold white]SUGGESTION:[/bold white] {result['suggestion']}")
    console.print()

    # Show triggered rules if any
    if result["triggered_rules"]:
        console.print("  [bold]WHY:[/bold]")

        if explain:
            # Verbose mode: show all rules with explanations
            for i, rule in enumerate(result["triggered_rules"]):
                prefix = "├─" if i < len(result["triggered_rules"]) - 1 else "└─"
                icon = _get_priority_icon(rule["priority"])
                console.print(f"  {prefix} {icon} {rule['explanation']}")
                if i < len(result["triggered_rules"]) - 1:
                    console.print("  │")
        else:
            # Compact mode: just show top 3 rules
            for i, rule in enumerate(result["triggered_rules"][:3]):
                prefix = (
                    "├─" if i < min(len(result["triggered_rules"]), 3) - 1 else "└─"
                )
                icon = _get_priority_icon(rule["priority"])
                console.print(f"  {prefix} {icon} {rule['explanation']}")
                if i < min(len(result["triggered_rules"]), 3) - 1:
                    console.print("  │")

        console.print()

    # Readiness snapshot
    if result["readiness"]:
        console.print("  [bold]READINESS SNAPSHOT:[/bold]")
        r = result["readiness"]

        sleep_bar = "█" * r["sleep"] + "░" * (5 - r["sleep"])
        stress_bar = "█" * r["stress"] + "░" * (5 - r["stress"])
        soreness_bar = "█" * r["soreness"] + "░" * (5 - r["soreness"])
        energy_bar = "█" * r["energy"] + "░" * (5 - r["energy"])

        console.print(
            f"  Sleep: {sleep_bar} {r['sleep']}    Stress: {stress_bar} {r['stress']}"
        )
        console.print(
            f"  Soreness: {soreness_bar} {r['soreness']}  Energy: {energy_bar} {r['energy']}"
        )

        score = r["composite_score"]
        score_label = _get_score_label(score)
        console.print(f"  Score: {score}/20 ({score_label})")
    else:
        console.print("  [dim]No readiness data logged yet[/dim]")
        console.print("  [dim]Run 'rivaflow readiness' to log today's check-in[/dim]")


def _get_priority_icon(priority: int) -> str:
    """Get icon based on rule priority."""
    if priority == 1:
        return "⚠️ "
    elif priority <= 3:
        return "📊"
    else:
        return "📹"


def _get_score_label(score: int) -> str:
    """Get label for readiness score."""
    if score >= 17:
        return "Excellent"
    elif score >= 14:
        return "Good"
    elif score >= 11:
        return "Moderate"
    elif score >= 8:
        return "Low"
    else:
        return "Very Low"
