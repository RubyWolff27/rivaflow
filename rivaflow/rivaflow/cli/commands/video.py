"""Video management commands."""
import json

import typer
from rich.console import Console
from rich.table import Table

from rivaflow.cli import prompts
from rivaflow.cli.utils.user_context import get_current_user_id
from rivaflow.core.services.video_service import VideoService

app = typer.Typer(help="Video library management")
console = Console()


@app.command()
def add(
    url: str = typer.Argument(..., help="Video URL"),
    title: str | None = typer.Option(None, "--title", "-t", help="Video title"),
    technique: str | None = typer.Option(
        None, "--technique", help="Technique name to link"
    ),
    timestamps: str | None = typer.Option(
        None,
        "--timestamps",
        help='Timestamps as JSON: [{"time": "2:30", "label": "entry"}]',
    ),
):
    """Add a video to the library."""
    user_id = get_current_user_id()
    service = VideoService()

    # Parse timestamps if provided
    timestamps_list = None
    if timestamps:
        try:
            timestamps_list = json.loads(timestamps)
        except json.JSONDecodeError:
            prompts.print_error("Invalid JSON format for timestamps")
            raise typer.Exit(1)

    # Add video
    video_id = service.add_video(
        user_id, url=url, title=title, timestamps=timestamps_list, technique_name=technique
    )

    # Display confirmation
    video = service.get_video(user_id, video_id)
    prompts.print_success(f"Video added (ID: {video_id})")
    console.print()
    console.print(service.format_video_summary(video))


@app.command()
def list(
    technique: str | None = typer.Option(
        None, "--technique", help="Filter by technique"
    ),
):
    """List all videos or filter by technique."""
    user_id = get_current_user_id()
    service = VideoService()

    if technique:
        videos = service.list_videos_by_technique(user_id, technique)
        title = f"Videos for '{technique}'"
    else:
        videos = service.list_all_videos(user_id)
        title = "Video Library"

    if not videos:
        console.print("[yellow]No videos found[/yellow]")
        return

    # Display as table
    console.print(f"[bold]{title}[/bold]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Title", style="white", max_width=40)
    table.add_column("Technique", style="cyan", max_width=20)
    table.add_column("Timestamps", style="dim", width=10)

    from rivaflow.db.repositories import TechniqueRepository

    tech_repo = TechniqueRepository()

    for video in videos:
        # Get technique name
        technique_name = ""
        if video.get("technique_id"):
            tech = tech_repo.get_by_id(video["technique_id"])
            if tech:
                technique_name = tech["name"]

        # Count timestamps
        timestamp_count = len(video.get("timestamps", []))

        table.add_row(
            str(video["id"]),
            video.get("title", "—")[:40],
            technique_name or "—",
            str(timestamp_count) if timestamp_count > 0 else "—",
        )

    console.print(table)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query (title or URL)"),
):
    """Search videos by title or URL."""
    service = VideoService()
    videos = service.search_videos(query)

    if not videos:
        console.print(f"[yellow]No videos found matching '{query}'[/yellow]")
        return

    console.print(f"[bold]Search results for '{query}':[/bold]\n")

    for video in videos:
        console.print(service.format_video_summary(video))
        console.print()


@app.command()
def delete(
    video_id: int = typer.Argument(..., help="Video ID to delete"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Delete a video from the library."""
    service = VideoService()

    # Get video to show what will be deleted
    video = service.get_video(video_id)
    if not video:
        prompts.print_error(f"Video ID {video_id} not found")
        raise typer.Exit(1)

    # Show video details
    console.print(service.format_video_summary(video))
    console.print()

    # Confirm deletion
    if not yes and not prompts.confirm("Delete this video?", default=False):
        prompts.print_info("Video not deleted")
        return

    # Delete
    service.delete_video(video_id)
    prompts.print_success(f"Video {video_id} deleted")
