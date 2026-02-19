"""Unit tests for VideoService — training video management."""

from unittest.mock import patch

from rivaflow.core.services.video_service import VideoService


class TestAddVideo:
    """Tests for VideoService.add_video."""

    @patch("rivaflow.core.services.video_service.TechniqueRepository")
    @patch("rivaflow.core.services.video_service.VideoRepository")
    def test_adds_video_without_technique(self, MockVideoRepo, MockTechRepo):
        """Should create video without technique link."""
        MockVideoRepo.return_value.create.return_value = 1

        service = VideoService()
        result = service.add_video(
            user_id=1, url="https://youtube.com/watch?v=abc", title="Guard pass"
        )

        assert result == 1
        MockVideoRepo.return_value.create.assert_called_once_with(
            url="https://youtube.com/watch?v=abc",
            title="Guard pass",
            timestamps=None,
            technique_id=None,
        )

    @patch("rivaflow.core.services.video_service.TechniqueRepository")
    @patch("rivaflow.core.services.video_service.VideoRepository")
    def test_adds_video_with_technique_link(self, MockVideoRepo, MockTechRepo):
        """Should resolve technique name and link to video."""
        MockTechRepo.return_value.get_or_create.return_value = {
            "id": 5,
            "name": "armbar",
        }
        MockVideoRepo.return_value.create.return_value = 2

        service = VideoService()
        result = service.add_video(
            user_id=1,
            url="https://youtube.com/watch?v=def",
            technique_name="armbar",
        )

        assert result == 2
        MockTechRepo.return_value.get_or_create.assert_called_once_with("armbar")
        MockVideoRepo.return_value.create.assert_called_once_with(
            url="https://youtube.com/watch?v=def",
            title=None,
            timestamps=None,
            technique_id=5,
        )

    @patch("rivaflow.core.services.video_service.TechniqueRepository")
    @patch("rivaflow.core.services.video_service.VideoRepository")
    def test_adds_video_with_timestamps(self, MockVideoRepo, MockTechRepo):
        """Should pass timestamps to repo."""
        MockVideoRepo.return_value.create.return_value = 3
        timestamps = [
            {"time": "0:30", "label": "Setup"},
            {"time": "1:15", "label": "Finish"},
        ]

        service = VideoService()
        service.add_video(
            user_id=1,
            url="https://youtube.com/watch?v=ghi",
            timestamps=timestamps,
        )

        call_kwargs = MockVideoRepo.return_value.create.call_args[1]
        assert call_kwargs["timestamps"] == timestamps


class TestGetVideo:
    """Tests for VideoService.get_video."""

    @patch("rivaflow.core.services.video_service.TechniqueRepository")
    @patch("rivaflow.core.services.video_service.VideoRepository")
    def test_returns_video_by_id(self, MockVideoRepo, MockTechRepo):
        """Should return video dict when found."""
        expected = {"id": 1, "url": "https://youtube.com/watch?v=abc", "title": "Test"}
        MockVideoRepo.return_value.get_by_id.return_value = expected

        service = VideoService()
        result = service.get_video(user_id=1, video_id=1)

        assert result == expected

    @patch("rivaflow.core.services.video_service.TechniqueRepository")
    @patch("rivaflow.core.services.video_service.VideoRepository")
    def test_returns_none_when_not_found(self, MockVideoRepo, MockTechRepo):
        """Should return None when video does not exist."""
        MockVideoRepo.return_value.get_by_id.return_value = None

        service = VideoService()
        result = service.get_video(user_id=1, video_id=999)

        assert result is None


class TestListAllVideos:
    """Tests for VideoService.list_all_videos."""

    @patch("rivaflow.core.services.video_service.TechniqueRepository")
    @patch("rivaflow.core.services.video_service.VideoRepository")
    def test_returns_all_videos(self, MockVideoRepo, MockTechRepo):
        """Should return list of all videos."""
        videos = [
            {"id": 1, "url": "https://youtube.com/1"},
            {"id": 2, "url": "https://youtube.com/2"},
        ]
        MockVideoRepo.return_value.list_all.return_value = videos

        service = VideoService()
        result = service.list_all_videos(user_id=1)

        assert len(result) == 2

    @patch("rivaflow.core.services.video_service.TechniqueRepository")
    @patch("rivaflow.core.services.video_service.VideoRepository")
    def test_returns_empty_list_when_no_videos(self, MockVideoRepo, MockTechRepo):
        """Should return empty list when no videos exist."""
        MockVideoRepo.return_value.list_all.return_value = []

        service = VideoService()
        result = service.list_all_videos(user_id=1)

        assert result == []


class TestListVideosByTechnique:
    """Tests for VideoService.list_videos_by_technique."""

    @patch("rivaflow.core.services.video_service.TechniqueRepository")
    @patch("rivaflow.core.services.video_service.VideoRepository")
    def test_returns_videos_for_technique(self, MockVideoRepo, MockTechRepo):
        """Should return videos linked to a technique."""
        MockTechRepo.return_value.get_by_name.return_value = {
            "id": 5,
            "name": "armbar",
        }
        MockVideoRepo.return_value.get_by_technique.return_value = [
            {"id": 1, "url": "https://youtube.com/1", "technique_id": 5}
        ]

        service = VideoService()
        result = service.list_videos_by_technique(user_id=1, technique_name="armbar")

        assert len(result) == 1
        MockVideoRepo.return_value.get_by_technique.assert_called_once_with(5)

    @patch("rivaflow.core.services.video_service.TechniqueRepository")
    @patch("rivaflow.core.services.video_service.VideoRepository")
    def test_returns_empty_when_technique_not_found(self, MockVideoRepo, MockTechRepo):
        """Should return empty list when technique name is unknown."""
        MockTechRepo.return_value.get_by_name.return_value = None

        service = VideoService()
        result = service.list_videos_by_technique(
            user_id=1, technique_name="nonexistent"
        )

        assert result == []
        MockVideoRepo.return_value.get_by_technique.assert_not_called()


class TestSearchVideos:
    """Tests for VideoService.search_videos."""

    @patch("rivaflow.core.services.video_service.TechniqueRepository")
    @patch("rivaflow.core.services.video_service.VideoRepository")
    def test_searches_videos_by_query(self, MockVideoRepo, MockTechRepo):
        """Should delegate search to video repo."""
        MockVideoRepo.return_value.search.return_value = [
            {"id": 1, "title": "Guard pass tutorial"}
        ]

        service = VideoService()
        result = service.search_videos(user_id=1, query="guard")

        assert len(result) == 1
        MockVideoRepo.return_value.search.assert_called_once_with(1, "guard")


class TestDeleteVideo:
    """Tests for VideoService.delete_video."""

    @patch("rivaflow.core.services.video_service.TechniqueRepository")
    @patch("rivaflow.core.services.video_service.VideoRepository")
    def test_deletes_video(self, MockVideoRepo, MockTechRepo):
        """Should call delete on the repo."""
        service = VideoService()
        service.delete_video(user_id=1, video_id=5)

        MockVideoRepo.return_value.delete.assert_called_once_with(5)


class TestFormatVideoSummary:
    """Tests for VideoService.format_video_summary."""

    @patch("rivaflow.core.services.video_service.TechniqueRepository")
    @patch("rivaflow.core.services.video_service.VideoRepository")
    def test_format_basic_video(self, MockVideoRepo, MockTechRepo):
        """Should format video with ID and URL."""
        service = VideoService()
        video = {"id": 1, "url": "https://youtube.com/1", "title": None}

        result = service.format_video_summary(video)

        assert "Video ID: 1" in result
        assert "https://youtube.com/1" in result

    @patch("rivaflow.core.services.video_service.TechniqueRepository")
    @patch("rivaflow.core.services.video_service.VideoRepository")
    def test_format_video_with_technique(self, MockVideoRepo, MockTechRepo):
        """Should include technique name when linked."""
        MockTechRepo.return_value.get_by_id.return_value = {
            "id": 5,
            "name": "armbar",
        }

        service = VideoService()
        video = {
            "id": 1,
            "url": "https://youtube.com/1",
            "title": "Armbar tutorial",
            "technique_id": 5,
        }

        result = service.format_video_summary(video)

        assert "armbar" in result
        assert "Armbar tutorial" in result

    @patch("rivaflow.core.services.video_service.TechniqueRepository")
    @patch("rivaflow.core.services.video_service.VideoRepository")
    def test_format_video_with_timestamps(self, MockVideoRepo, MockTechRepo):
        """Should format timestamps when present."""
        service = VideoService()
        video = {
            "id": 1,
            "url": "https://youtube.com/1",
            "title": None,
            "timestamps": [
                {"time": "0:30", "label": "Setup"},
                {"time": "1:15", "label": "Finish"},
            ],
        }

        result = service.format_video_summary(video)

        assert "0:30" in result
        assert "Setup" in result
        assert "Finish" in result
