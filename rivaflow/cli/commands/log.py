"""Session logging commands."""
import typer
import json
import random
from datetime import date
from typing import Optional
from rich.prompt import Prompt

from rivaflow.cli import prompts
from rivaflow.cli.utils.user_context import get_current_user_id
from rivaflow.cli.utils.error_handler import handle_error, require_login
from rivaflow.core.services.session_service import SessionService
from rivaflow.core.services.streak_service import StreakService
from rivaflow.core.services.milestone_service import MilestoneService
from rivaflow.core.services.insight_service import InsightService
from rivaflow.db.repositories import VideoRepository, CheckinRepository
from rivaflow.config import ALL_CLASS_TYPES, DEFAULT_DURATION, DEFAULT_INTENSITY, TOMORROW_INTENTIONS, MILESTONE_QUOTES

app = typer.Typer(help="Log training sessions")


@app.command()
def log(
    quick: bool = typer.Option(False, "--quick", "-q", help="Quick mode: minimal inputs only"),
):
    """Log a training session."""
    try:
        # Ensure user is logged in
        require_login()

        service = SessionService()
        video_repo = VideoRepository()

        # Get autocomplete data
        autocomplete = service.get_autocomplete_data()

        if quick:
            _quick_log(service, autocomplete)
        else:
            _full_log(service, video_repo, autocomplete)
    except Exception as e:
        handle_error(e, context="logging training session")


def _quick_log(service: SessionService, autocomplete: dict):
    """Quick session logging (< 20 seconds target)."""
    try:
        user_id = get_current_user_id()
        prompts.console.print("[bold]Quick Session Log[/bold]\n")

        # 1. Gym
        gym_name = prompts.prompt_text(
            "Gym name", autocomplete=autocomplete.get("gyms", [])
        )

        # 2. Class type
        class_type = prompts.prompt_choice(
            "Class type", choices=sorted(ALL_CLASS_TYPES), default="gi"
        )

        # 3. Rolls (if applicable)
        rolls = 0
        if service.is_sparring_class(class_type):
            rolls = prompts.prompt_int("Rolls", default=0, min_val=0, max_val=50)

        # Create with defaults
        session_id = service.create_session(
            user_id=user_id,
            session_date=date.today(),
            class_type=class_type,
            gym_name=gym_name,
            duration_mins=DEFAULT_DURATION,
            intensity=DEFAULT_INTENSITY,
            rolls=rolls,
        )

        # Display summary
        session = service.get_session(user_id, session_id)
        prompts.console.print()
        prompts.print_success("Session logged!")
        prompts.console.print(service.format_session_summary(session))

        # Engagement features (v0.2)
        _add_engagement_features(session_id)
    except Exception as e:
        handle_error(e, context="saving quick session")


def _full_log(service: SessionService, video_repo: VideoRepository, autocomplete: dict):
    """Full interactive session logging (< 60 seconds target)."""
    user_id = get_current_user_id()
    prompts.console.print("[bold]Session Log[/bold]\n")

    # 1. Class type
    class_type = prompts.prompt_choice(
        "Class type", choices=sorted(ALL_CLASS_TYPES), default="gi"
    )

    # 2. Gym
    gym_name = prompts.prompt_text(
        "Gym name", autocomplete=autocomplete.get("gyms", [])
    )

    # 3. Location
    location = prompts.prompt_text(
        "Location (optional)", autocomplete=autocomplete.get("locations", [])
    )
    if not location:
        location = None

    # 4. Duration
    duration_mins = prompts.prompt_int(
        "Duration (minutes)", default=DEFAULT_DURATION, min_val=1, max_val=480
    )

    # 5. Intensity
    intensity = prompts.prompt_int(
        "Intensity (1-5)", default=DEFAULT_INTENSITY, min_val=1, max_val=5
    )

    # 6-8. Sparring details (if applicable)
    rolls = 0
    subs_for = 0
    subs_against = 0
    if service.is_sparring_class(class_type):
        rolls = prompts.prompt_int("Rolls", default=0, min_val=0, max_val=50)
        if rolls > 0:
            subs_for = prompts.prompt_int(
                "Submissions for", default=0, min_val=0, max_val=50
            )
            subs_against = prompts.prompt_int(
                "Submissions against", default=0, min_val=0, max_val=50
            )

    # 9. Techniques (with recall cards)
    techniques_list = prompts.prompt_list(
        "Techniques (comma-separated, optional)",
        autocomplete=autocomplete.get("techniques", []),
        optional=True,
    )

    # Show recall cards for techniques with videos
    if techniques_list:
        from rivaflow.db.repositories import TechniqueRepository

        tech_repo = TechniqueRepository()
        prompts.console.print()
        for tech_name in techniques_list:
            tech = tech_repo.get_by_name(tech_name)
            if tech:
                videos = video_repo.get_by_technique(tech["id"])
                if videos:
                    prompts.display_recall_card(tech_name, videos)

    # 10. Partners
    partners_list = prompts.prompt_list(
        "Partners (comma-separated, optional)",
        autocomplete=autocomplete.get("partners", []),
        optional=True,
    )

    # 11. Notes
    prompts.console.print()
    notes = prompts.prompt_text("Notes (optional)")
    if not notes:
        notes = None

    # Confirm
    prompts.console.print()
    if not prompts.confirm("Save session?", default=True):
        prompts.print_info("Session not saved")
        return

    # Create session
    session_id = service.create_session(
        user_id=user_id,
        session_date=date.today(),
        class_type=class_type,
        gym_name=gym_name,
        location=location,
        duration_mins=duration_mins,
        intensity=intensity,
        rolls=rolls,
        submissions_for=subs_for,
        submissions_against=subs_against,
        partners=partners_list,
        techniques=techniques_list,
        notes=notes,
    )

    # Display summary
    session = service.get_session(user_id, session_id)
    prompts.console.print()
    prompts.print_success("Session logged!")
    prompts.console.print()
    prompts.console.print(service.format_session_summary(session))

    # Engagement features (v0.2)
    _add_engagement_features(session_id)

def _add_engagement_features(session_id: int):
    """Add engagement features after session logging (v0.2)."""
    user_id = get_current_user_id()
    checkin_repo = CheckinRepository()
    streak_service = StreakService()
    milestone_service = MilestoneService()
    insight_service = InsightService()

    today = date.today()

    # 1. Create check-in record
    insight = insight_service.generate_insight(user_id)
    insight_json = json.dumps(insight)

    checkin_id = checkin_repo.upsert_checkin(
        user_id=user_id,
        check_date=today,
        checkin_type="session",
        session_id=session_id,
        insight_shown=insight_json
    )

    # 2. Update streaks
    streak_info = streak_service.record_checkin(user_id, "session", today)

    # 3. Check for new milestones
    new_milestones = milestone_service.check_all_milestones(user_id)

    # Display streak update
    prompts.console.print()
    checkin_streak = streak_info["checkin_streak"]
    streak_text = f"  🔥 [bold yellow]Streak: {checkin_streak['current_streak']} days"

    if streak_info["streak_extended"]:
        streak_text += " (+1)"

    if streak_info["grace_day_used"]:
        streak_text += " [dim](used grace day)[/dim]"

    if streak_info["longest_beaten"]:
        streak_text += " [green]🎉 New personal best![/green]"

    streak_text += "[/bold yellow]"
    prompts.console.print(streak_text)
    prompts.console.print()

    # Display insight
    prompts.console.print(f"  [bold]{insight.get('icon', '💡')} {insight.get('title', 'INSIGHT').upper()}:[/bold]")
    prompts.console.print(f"  [dim]{insight.get('message', '')}[/dim]")
    if insight.get('action'):
        prompts.console.print(f"  [dim italic]{insight['action']}[/dim italic]")
    prompts.console.print()

    # Celebrate milestones
    if new_milestones:
        from rich.panel import Panel

        for milestone in new_milestones:
            quote, author = random.choice(MILESTONE_QUOTES)
            bar = "█" * 30

            celebration = f"""
  [bold yellow]{bar}[/bold yellow]  [bold white]{milestone['milestone_label'].upper()}[/bold white]

  [italic]"{quote}"[/italic]
                                        [dim]— {author}[/dim]

  [bold green]🏆 Achievement unlocked:[/bold green] {milestone['achieved_at'][:10]}
"""

            # Get next milestone
            totals = milestone_service.get_current_totals(user_id)
            current = totals.get(milestone['milestone_type'], 0)
            next_ms = milestone_service.milestone_repo.get_next_milestone(user_id, milestone['milestone_type'], current)

            if next_ms:
                celebration += f"\n  Next milestone: {next_ms['milestone_label']} ({next_ms['remaining']} to go)"

            panel = Panel(
                celebration,
                title="[bold yellow]🎉 MILESTONE UNLOCKED![/bold yellow]",
                border_style="yellow",
                padding=(1, 2),
            )
            prompts.console.print(panel)
            prompts.console.print()

            # Mark as celebrated
            milestone_service.mark_celebrated(milestone["id"])

    # Tomorrow's intention prompt
    prompts.console.print("  [bold]What's the plan for tomorrow?[/bold]")
    prompts.console.print()
    prompts.console.print("  [cyan]1[/cyan] 🥋 Gi   [cyan]2[/cyan] 🩳 No-Gi   [cyan]3[/cyan] 😴 Rest   [cyan]4[/cyan] 🤷 Not sure")
    prompts.console.print()

    choice = Prompt.ask("  Select", choices=["1", "2", "3", "4"], default="4", show_default=False)

    intention_map = {
        "1": "train_gi",
        "2": "train_nogi",
        "3": "rest",
        "4": "unsure",
    }

    intention = intention_map.get(choice, "unsure")

    # Update check-in with tomorrow's intention
    checkin_repo.update_tomorrow_intention(user_id, today, intention)

    intention_label = TOMORROW_INTENTIONS.get(intention, intention)
    prompts.console.print()
    prompts.console.print(f"  [green]✅ Tomorrow:[/green] {intention_label}")
    prompts.console.print()
