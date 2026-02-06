"""Readiness check-in commands."""

import json
from datetime import date, datetime
from typing import Optional

import typer

from rivaflow.cli import prompts
from rivaflow.cli.utils.error_handler import handle_error, require_login
from rivaflow.cli.utils.user_context import get_current_user_id
from rivaflow.core.services.insight_service import InsightService
from rivaflow.core.services.milestone_service import MilestoneService
from rivaflow.core.services.readiness_service import ReadinessService
from rivaflow.core.services.streak_service import StreakService
from rivaflow.db.repositories.checkin_repo import CheckinRepository

app = typer.Typer(help="Daily readiness check-in")


@app.command()
def readiness(
    check_date: Optional[str] = typer.Option(
        None,
        "--date",
        "-d",
        help="Date for check-in (YYYY-MM-DD). Defaults to today.",
    ),
):
    """
    Log daily readiness check-in to monitor recovery.

    \b
    Track four key metrics (1-5 scale):
      • Sleep quality
      • Stress level
      • Muscle soreness
      • Energy level

    \b
    Optional tracking:
      • Body weight (kg)
      • Injury/hotspot notes

    \b
    Examples:
      # Log today's readiness
      $ rivaflow readiness

      # Log readiness for a specific date
      $ rivaflow readiness --date 2026-02-01
      $ rivaflow readiness -d 2026-02-01
    """
    try:
        # Ensure user is logged in
        require_login()

        user_id = get_current_user_id()
        service = ReadinessService()

        # Parse date
        if check_date:
            try:
                target_date = datetime.strptime(check_date, "%Y-%m-%d").date()
            except ValueError:
                prompts.print_error(
                    "Invalid date format. Use YYYY-MM-DD (e.g., 2026-02-01)"
                )
                prompts.console.print(
                    "[dim]Example: rivaflow readiness --date 2026-01-31[/dim]"
                )
                raise typer.Exit(1)

            # Validate date is not in the future
            if target_date > date.today():
                prompts.print_error(
                    f"Cannot log readiness for future dates (today is {date.today()})"
                )
                raise typer.Exit(1)
        else:
            target_date = date.today()

        # Check if already logged for this date
        existing = service.get_readiness(user_id, target_date)
        if existing:
            prompts.console.print(
                f"[yellow]⚠ Readiness already logged for {target_date}. Updating existing entry...[/yellow]\n"
            )

        # Prompt for readiness metrics
        prompts.console.print(f"[bold]Readiness Check-in: {target_date}[/bold]\n")

        sleep = prompts.prompt_int(
            "How did you sleep? (1-5)", default=3, min_val=1, max_val=5
        )
        stress = prompts.prompt_int(
            "Stress level? (1-5)", default=3, min_val=1, max_val=5
        )
        soreness = prompts.prompt_int(
            "Soreness level? (1-5)", default=2, min_val=1, max_val=5
        )
        energy = prompts.prompt_int(
            "Energy level? (1-5)", default=3, min_val=1, max_val=5
        )

        hotspot_note = prompts.prompt_text(
            "Any hotspots? (injury/soreness location, optional)"
        )
        if not hotspot_note:
            hotspot_note = None

        # Save readiness
        service.log_readiness(
            user_id=user_id,
            check_date=target_date,
            sleep=sleep,
            stress=stress,
            soreness=soreness,
            energy=energy,
            hotspot_note=hotspot_note,
        )

        # Display summary
        readiness_entry = service.get_readiness(user_id, target_date)
        prompts.console.print()
        prompts.console.print(service.format_readiness_summary(readiness_entry))

        # Engagement features (v0.2) - only for today's check-ins
        if target_date == date.today():
            _add_engagement_features_readiness(user_id, readiness_entry["id"])
    except Exception as e:
        handle_error(e, context="logging readiness check-in")


def _add_engagement_features_readiness(user_id: int, readiness_id: int):
    """Add engagement features after readiness check-in (v0.2)."""
    checkin_repo = CheckinRepository()
    streak_service = StreakService()
    milestone_service = MilestoneService()
    insight_service = InsightService()

    today = date.today()

    # Check if already checked in today (session takes priority)
    existing_checkin = checkin_repo.get_checkin(user_id, today)

    if existing_checkin and existing_checkin["checkin_type"] == "session":
        # Already logged a session today, don't duplicate engagement
        return

    # Process engagement features with progress indicator
    with prompts.console.status(
        "[cyan]Calculating streaks and milestones...", spinner="dots"
    ):
        # 1. Create/update check-in record
        insight = insight_service.generate_insight(user_id)
        insight_json = json.dumps(insight)

        checkin_repo.upsert_checkin(
            user_id=user_id,
            check_date=today,
            checkin_type=(
                "readiness_only"
                if not existing_checkin
                else existing_checkin["checkin_type"]
            ),
            readiness_id=readiness_id,
            insight_shown=insight_json,
        )

        # 2. Update streaks (check-in + readiness)
        streak_info = streak_service.record_checkin(user_id, "readiness_only", today)
        readiness_streak_info = streak_service.record_readiness_checkin(user_id, today)

        # 3. Check for new milestones
        milestone_service.check_all_milestones(user_id)

    # Display streak update
    prompts.console.print()
    checkin_streak = streak_info["checkin_streak"]
    readiness_streak = readiness_streak_info["readiness_streak"]

    prompts.console.print(
        f"  🔥 [bold yellow]Check-in streak: {checkin_streak['current_streak']} days[/bold yellow]"
    )
    prompts.console.print(
        f"  💚 [bold green]Readiness streak: {readiness_streak['current_streak']} days[/bold green]"
    )
    prompts.console.print()

    # Display insight
    prompts.console.print(
        f"  [bold]{insight.get('icon', '💡')} {insight.get('title', 'INSIGHT').upper()}:[/bold]"
    )
    prompts.console.print(f"  [dim]{insight.get('message', '')}[/dim]")
    if insight.get("action"):
        prompts.console.print(f"  [dim italic]{insight['action']}[/dim italic]")
    prompts.console.print()

    # Show today's recommendation based on readiness
    from rivaflow.core.services.suggestion_engine import SuggestionEngine

    engine = SuggestionEngine()
    try:
        result = engine.get_suggestion()
        prompts.console.print("  [bold]TODAY'S RECOMMENDATION:[/bold]")
        prompts.console.print(f"  [cyan]{result['suggestion']}[/cyan]")
        prompts.console.print()
    except Exception:
        # Suggestion engine might fail if no data - skip silently
        pass
