"""Session logging commands."""
import typer
from datetime import date
from typing import Optional

from rivaflow.cli import prompts
from rivaflow.core.services.session_service import SessionService
from rivaflow.db.repositories import VideoRepository
from rivaflow.config import ALL_CLASS_TYPES, DEFAULT_DURATION, DEFAULT_INTENSITY

app = typer.Typer(help="Log training sessions")


@app.command()
def log(
    quick: bool = typer.Option(False, "--quick", "-q", help="Quick mode: minimal inputs only"),
):
    """Log a training session."""
    service = SessionService()
    video_repo = VideoRepository()

    # Get autocomplete data
    autocomplete = service.get_autocomplete_data()

    if quick:
        _quick_log(service, autocomplete)
    else:
        _full_log(service, video_repo, autocomplete)


def _quick_log(service: SessionService, autocomplete: dict):
    """Quick session logging (< 20 seconds target)."""
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
        session_date=date.today(),
        class_type=class_type,
        gym_name=gym_name,
        duration_mins=DEFAULT_DURATION,
        intensity=DEFAULT_INTENSITY,
        rolls=rolls,
    )

    # Display summary
    session = service.get_session(session_id)
    prompts.console.print()
    prompts.print_success("Session logged!")
    prompts.console.print(service.format_session_summary(session))


def _full_log(service: SessionService, video_repo: VideoRepository, autocomplete: dict):
    """Full interactive session logging (< 60 seconds target)."""
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
    session = service.get_session(session_id)
    prompts.console.print()
    prompts.print_success("Session logged!")
    prompts.console.print()
    prompts.console.print(service.format_session_summary(session))
