"""Service layer for video management."""

from rivaflow.db.repositories import TechniqueRepository, VideoRepository


class VideoService:
    """Business logic for training video management."""

    def __init__(self):
        self.video_repo = VideoRepository()
        self.technique_repo = TechniqueRepository()

    def add_video(
        self,
        user_id: int,
        url: str,
        title: str | None = None,
        timestamps: list[dict] | None = None,
        technique_name: str | None = None,
    ) -> int:
        """
        Add a new video to the library.
        Returns video ID.
        """
        technique_id = None
        if technique_name:
            technique = self.technique_repo.get_or_create(technique_name)
            technique_id = technique["id"]

        return self.video_repo.create(
            user_id=user_id, url=url, title=title, timestamps=timestamps, technique_id=technique_id
        )

    def get_video(self, user_id: int, video_id: int) -> dict | None:
        """Get a video by ID."""
        # Videos are a shared resource, not user-specific
        return self.video_repo.get_by_id(video_id)

    def list_all_videos(self, user_id: int) -> list[dict]:
        """Get all videos."""
        # Videos are a shared resource, not user-specific
        return self.video_repo.list_all()

    def list_videos_by_technique(self, user_id: int, technique_name: str) -> list[dict]:
        """Get all videos for a specific technique."""
        technique = self.technique_repo.get_by_name(technique_name)
        if not technique:
            return []

        return self.video_repo.get_by_technique(user_id, technique["id"])

    def search_videos(self, user_id: int, query: str) -> list[dict]:
        """Search videos by title or URL."""
        return self.video_repo.search(user_id, query)

    def delete_video(self, user_id: int, video_id: int) -> None:
        """Delete a video by ID."""
        self.video_repo.delete(user_id, video_id)

    def format_video_summary(self, video: dict) -> str:
        """Format a video as a human-readable summary."""
        lines = [f"Video ID: {video['id']}"]

        if video.get("title"):
            lines.append(f"  Title: {video['title']}")

        lines.append(f"  URL: {video['url']}")

        if video.get("technique_id"):
            # Get technique name
            technique = self.technique_repo.get_by_id(video["technique_id"])
            if technique:
                lines.append(f"  Technique: {technique['name']}")

        if video.get("timestamps"):
            lines.append("  Timestamps:")
            for ts in video["timestamps"]:
                lines.append(f"    → {ts['time']} - {ts['label']}")

        return "\n".join(lines)
