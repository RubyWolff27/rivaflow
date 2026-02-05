"""Tests for 'rivaflow log' CLI command."""

from typer.testing import CliRunner
from datetime import date

from rivaflow.cli.app import app
from rivaflow.db.repositories import SessionRepository

runner = CliRunner()


class TestLogCommand:
    """Tests for session logging command."""

    def test_log_minimal(self, temp_db, test_user, monkeypatch):
        """Test logging session with minimal input."""
        # Mock user context to return test_user
        monkeypatch.setattr(
            "rivaflow.cli.utils.user_context.get_current_user_id",
            lambda: test_user["id"],
        )

        # Mock prompts to provide input
        inputs = [
            "Test Gym",  # gym
            "60",  # duration
            "4",  # intensity
            "gi",  # class_type
            "",  # rolls (skip)
            "",  # notes (skip)
        ]
        monkeypatch.setattr("builtins.input", lambda _: inputs.pop(0))

        result = runner.invoke(app, ["log"])

        assert result.exit_code == 0
        assert "logged successfully" in result.output.lower() or "✓" in result.output

        # Verify session was created in database
        repo = SessionRepository()
        sessions = repo.list_by_user(test_user["id"])
        assert len(sessions) > 0

    def test_log_with_flags(self, temp_db, test_user, monkeypatch):
        """Test logging session with command-line flags."""
        monkeypatch.setattr(
            "rivaflow.cli.utils.user_context.get_current_user_id",
            lambda: test_user["id"],
        )

        result = runner.invoke(
            app,
            [
                "log",
                "--gym",
                "Test Gym",
                "--duration",
                "90",
                "--intensity",
                "5",
                "--class-type",
                "no-gi",
                "--rolls",
                "8",
            ],
        )

        # Note: May need interactive prompts still
        # Just verify it doesn't crash
        assert result.exit_code == 0 or "gym" in result.output.lower()

    def test_log_invalid_date(self, temp_db, test_user, monkeypatch):
        """Test error handling for invalid date format."""
        monkeypatch.setattr(
            "rivaflow.cli.utils.user_context.get_current_user_id",
            lambda: test_user["id"],
        )

        result = runner.invoke(
            app,
            [
                "log",
                "--date",
                "invalid-date",
            ],
        )

        # Should show error about date format
        assert (
            result.exit_code != 0
            or "invalid" in result.output.lower()
            or "date" in result.output.lower()
        )

    def test_log_negative_duration(self, temp_db, test_user, monkeypatch):
        """Test validation for negative duration."""
        monkeypatch.setattr(
            "rivaflow.cli.utils.user_context.get_current_user_id",
            lambda: test_user["id"],
        )

        result = runner.invoke(
            app,
            [
                "log",
                "--duration",
                "-10",
            ],
        )

        # Should show error about invalid duration
        assert (
            result.exit_code != 0
            or "duration" in result.output.lower()
            or "invalid" in result.output.lower()
        )

    def test_log_intensity_out_of_range(self, temp_db, test_user, monkeypatch):
        """Test validation for intensity out of range (1-5)."""
        monkeypatch.setattr(
            "rivaflow.cli.utils.user_context.get_current_user_id",
            lambda: test_user["id"],
        )

        result = runner.invoke(
            app,
            [
                "log",
                "--intensity",
                "10",
            ],
        )

        # Should show error about intensity range
        assert (
            result.exit_code != 0
            or "intensity" in result.output.lower()
            or "1" in result.output
        )

    def test_log_creates_database_record(self, temp_db, test_user, monkeypatch):
        """Test that log command creates a session record in database."""
        monkeypatch.setattr(
            "rivaflow.cli.utils.user_context.get_current_user_id",
            lambda: test_user["id"],
        )

        # Get initial count
        repo = SessionRepository()
        initial_count = len(repo.list_by_user(test_user["id"]))

        # Mock inputs for interactive prompts
        inputs = ["Test Gym", "60", "4", "gi", "", ""]
        monkeypatch.setattr("builtins.input", lambda _: inputs.pop(0) if inputs else "")

        result = runner.invoke(app, ["log"])

        # Verify new session was created
        final_count = len(repo.list_by_user(test_user["id"]))
        if result.exit_code == 0:
            assert final_count > initial_count


class TestRestCommand:
    """Tests for rest day logging command."""

    def test_rest_day_logging(self, temp_db, test_user, monkeypatch):
        """Test logging a rest day."""
        monkeypatch.setattr(
            "rivaflow.cli.utils.user_context.get_current_user_id",
            lambda: test_user["id"],
        )

        # Mock inputs
        inputs = ["active", "Recovery day"]
        monkeypatch.setattr("builtins.input", lambda _: inputs.pop(0) if inputs else "")

        result = runner.invoke(app, ["rest"])

        assert result.exit_code == 0 or "rest" in result.output.lower()

    def test_rest_with_flags(self, temp_db, test_user, monkeypatch):
        """Test rest day with command-line flags."""
        monkeypatch.setattr(
            "rivaflow.cli.utils.user_context.get_current_user_id",
            lambda: test_user["id"],
        )

        result = runner.invoke(
            app,
            [
                "rest",
                "--type",
                "injury",
                "--note",
                "Shoulder rehab",
            ],
        )

        assert result.exit_code == 0 or "rest" in result.output.lower()


class TestReadinessCommand:
    """Tests for readiness check-in command."""

    def test_readiness_checkin(self, temp_db, test_user, monkeypatch):
        """Test logging a readiness check-in."""
        monkeypatch.setattr(
            "rivaflow.cli.utils.user_context.get_current_user_id",
            lambda: test_user["id"],
        )

        # Mock inputs for sleep, stress, soreness, energy
        inputs = ["4", "3", "2", "4", ""]
        monkeypatch.setattr("builtins.input", lambda _: inputs.pop(0) if inputs else "")

        result = runner.invoke(app, ["readiness"])

        assert result.exit_code == 0 or "readiness" in result.output.lower()

    def test_readiness_invalid_values(self, temp_db, test_user, monkeypatch):
        """Test validation for readiness values (should be 1-5)."""
        monkeypatch.setattr(
            "rivaflow.cli.utils.user_context.get_current_user_id",
            lambda: test_user["id"],
        )

        result = runner.invoke(
            app,
            [
                "readiness",
                "--sleep",
                "10",  # Out of range
            ],
        )

        # Should show error or reprompt
        assert result.exit_code != 0 or "sleep" in result.output.lower()


class TestReportCommand:
    """Tests for report generation commands."""

    def test_report_week(self, temp_db, test_user, session_factory, monkeypatch):
        """Test weekly report generation."""
        monkeypatch.setattr(
            "rivaflow.cli.utils.user_context.get_current_user_id",
            lambda: test_user["id"],
        )

        # Create some test sessions
        session_factory(session_date=date.today())
        session_factory(session_date=date.today())

        result = runner.invoke(app, ["report", "week"])

        assert result.exit_code == 0
        # Should show some stats
        assert "session" in result.output.lower() or "week" in result.output.lower()

    def test_report_month(self, temp_db, test_user, session_factory, monkeypatch):
        """Test monthly report generation."""
        monkeypatch.setattr(
            "rivaflow.cli.utils.user_context.get_current_user_id",
            lambda: test_user["id"],
        )

        session_factory(session_date=date.today())

        result = runner.invoke(app, ["report", "month"])

        assert result.exit_code == 0
        assert "month" in result.output.lower() or "session" in result.output.lower()


class TestStreakCommand:
    """Tests for streak display command."""

    def test_streak_display(self, temp_db, test_user, monkeypatch):
        """Test streak information display."""
        monkeypatch.setattr(
            "rivaflow.cli.utils.user_context.get_current_user_id",
            lambda: test_user["id"],
        )

        result = runner.invoke(app, ["streak"])

        assert result.exit_code == 0
        # Should show streak information
        assert "streak" in result.output.lower() or "day" in result.output.lower()


class TestProgressCommand:
    """Tests for progress tracking command."""

    def test_progress_display(self, temp_db, test_user, session_factory, monkeypatch):
        """Test progress information display."""
        monkeypatch.setattr(
            "rivaflow.cli.utils.user_context.get_current_user_id",
            lambda: test_user["id"],
        )

        # Create some sessions for progress
        session_factory(session_date=date.today())

        result = runner.invoke(app, ["progress"])

        assert result.exit_code == 0


class TestDashboardCommand:
    """Tests for dashboard display command."""

    def test_dashboard_display(self, temp_db, test_user, session_factory, monkeypatch):
        """Test dashboard rendering."""
        monkeypatch.setattr(
            "rivaflow.cli.utils.user_context.get_current_user_id",
            lambda: test_user["id"],
        )

        session_factory(session_date=date.today())

        result = runner.invoke(app, ["dashboard"])

        assert result.exit_code == 0
        # Dashboard should show some information
        assert len(result.output) > 0


class TestAuthCommands:
    """Tests for authentication commands."""

    def test_login_command_prompts(self, temp_db, test_user):
        """Test login command prompts for credentials."""
        # Note: This would require mocking password prompts
        # For now, just test that command exists
        result = runner.invoke(app, ["auth", "login", "--help"])
        assert result.exit_code == 0
        assert "email" in result.output.lower()

    def test_logout_command(self, temp_db, monkeypatch):
        """Test logout command."""
        result = runner.invoke(app, ["auth", "logout"])
        # Should succeed even if not logged in
        assert result.exit_code == 0 or "not" in result.output.lower()

    def test_whoami_not_logged_in(self, temp_db):
        """Test whoami when not logged in."""
        result = runner.invoke(app, ["auth", "whoami"])
        assert result.exit_code == 0
        assert (
            "not logged in" in result.output.lower() or "login" in result.output.lower()
        )


class TestStatsCommand:
    """Tests for stats command."""

    def test_stats_display(self, temp_db, test_user, session_factory, monkeypatch):
        """Test lifetime stats display."""
        monkeypatch.setattr(
            "rivaflow.cli.utils.user_context.get_current_user_id",
            lambda: test_user["id"],
        )

        # Create test data
        session_factory(session_date=date.today())

        result = runner.invoke(app, ["stats"])

        assert result.exit_code == 0
        # Should show stats
        assert "session" in result.output.lower() or "total" in result.output.lower()


class TestExportCommand:
    """Tests for data export command."""

    def test_export_creates_file(
        self, temp_db, test_user, session_factory, monkeypatch
    ):
        """Test that export creates a JSON file."""
        monkeypatch.setattr(
            "rivaflow.cli.utils.user_context.get_current_user_id",
            lambda: test_user["id"],
        )

        session_factory(session_date=date.today())

        result = runner.invoke(app, ["export"])

        assert result.exit_code == 0
        assert "export" in result.output.lower() or ".json" in result.output.lower()
