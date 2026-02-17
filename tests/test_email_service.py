"""Unit tests for EmailService."""

import os
from unittest.mock import MagicMock, patch

from rivaflow.core.services.email_service import EmailService


class TestEmailServiceInit:
    """Tests for EmailService initialization and configuration."""

    def test_not_configured_when_no_env_vars(self):
        """Service should be disabled when no env vars are set."""
        with patch.dict(
            os.environ,
            {},
            clear=True,
        ):
            # Remove any existing keys
            env = {
                k: v
                for k, v in os.environ.items()
                if k not in ("SENDGRID_API_KEY", "SMTP_USER", "SMTP_PASSWORD")
            }
            with patch.dict(os.environ, env, clear=True):
                service = EmailService()
                assert service.enabled is False
                assert service.method is None

    def test_configured_with_sendgrid(self):
        """Service should use SendGrid when SENDGRID_API_KEY is set."""
        with patch.dict(
            os.environ,
            {"SENDGRID_API_KEY": "SG.test-key-123"},
            clear=False,
        ):
            service = EmailService()
            assert service.enabled is True
            assert service.method == "sendgrid"

    def test_configured_with_smtp(self):
        """Service should use SMTP when SMTP credentials are set."""
        env = {k: v for k, v in os.environ.items() if k != "SENDGRID_API_KEY"}
        env["SMTP_USER"] = "user@test.com"
        env["SMTP_PASSWORD"] = "password123"
        with patch.dict(os.environ, env, clear=True):
            service = EmailService()
            assert service.enabled is True
            assert service.method == "smtp"

    def test_sendgrid_takes_priority_over_smtp(self):
        """SendGrid should be preferred when both are configured."""
        with patch.dict(
            os.environ,
            {
                "SENDGRID_API_KEY": "SG.test-key",
                "SMTP_USER": "user@test.com",
                "SMTP_PASSWORD": "password123",
            },
            clear=False,
        ):
            service = EmailService()
            assert service.method == "sendgrid"

    def test_default_from_name(self):
        """Default from_name should be RivaFlow."""
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ("SENDGRID_API_KEY", "FROM_NAME")
        }
        env["SMTP_USER"] = "user@test.com"
        env["SMTP_PASSWORD"] = "pass"
        with patch.dict(os.environ, env, clear=True):
            service = EmailService()
            assert service.from_name == "RivaFlow"


class TestSendEmailNotConfigured:
    """Tests for send_email when service is not configured."""

    def test_send_returns_false_when_not_configured(self):
        """send_email should return False when service is disabled."""
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ("SENDGRID_API_KEY", "SMTP_USER", "SMTP_PASSWORD")
        }
        with patch.dict(os.environ, env, clear=True):
            service = EmailService()
            result = service.send_email(
                to_email="user@example.com",
                subject="Test",
                html_content="<p>Hello</p>",
            )
            assert result is False

    def test_send_password_reset_returns_false_when_not_configured(self):
        """send_password_reset_email should return False when disabled."""
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ("SENDGRID_API_KEY", "SMTP_USER", "SMTP_PASSWORD")
        }
        with patch.dict(os.environ, env, clear=True):
            service = EmailService()
            result = service.send_password_reset_email(
                to_email="user@example.com",
                reset_token="abc123",
            )
            assert result is False


class TestSendViaSendGrid:
    """Tests for SendGrid email sending with mocked SendGrid client."""

    def _make_sendgrid_service(self):
        """Create an EmailService configured for SendGrid."""
        with patch.dict(
            os.environ,
            {"SENDGRID_API_KEY": "SG.fake-key"},
            clear=False,
        ):
            return EmailService()

    @patch("rivaflow.core.services.email_service.EmailService._send_via_sendgrid")
    def test_send_email_calls_sendgrid(self, mock_sendgrid):
        """send_email should delegate to _send_via_sendgrid."""
        mock_sendgrid.return_value = True
        service = self._make_sendgrid_service()

        result = service.send_email(
            to_email="user@example.com",
            subject="Test Subject",
            html_content="<p>Hello</p>",
        )
        assert result is True
        mock_sendgrid.assert_called_once_with(
            "user@example.com",
            "Test Subject",
            "<p>Hello</p>",
            None,
        )

    @patch("rivaflow.core.services.email_service.EmailService._send_via_sendgrid")
    def test_send_email_with_text_content(self, mock_sendgrid):
        """send_email should pass text_content to _send_via_sendgrid."""
        mock_sendgrid.return_value = True
        service = self._make_sendgrid_service()

        result = service.send_email(
            to_email="user@example.com",
            subject="Test",
            html_content="<p>Hello</p>",
            text_content="Hello plain",
        )
        assert result is True
        mock_sendgrid.assert_called_once_with(
            "user@example.com",
            "Test",
            "<p>Hello</p>",
            "Hello plain",
        )

    @patch("rivaflow.core.services.email_service.EmailService._send_via_sendgrid")
    def test_sendgrid_failure_returns_false(self, mock_sendgrid):
        """send_email should return False when SendGrid fails."""
        mock_sendgrid.return_value = False
        service = self._make_sendgrid_service()

        result = service.send_email(
            to_email="user@example.com",
            subject="Test",
            html_content="<p>Hello</p>",
        )
        assert result is False


class TestSendViaSmtp:
    """Tests for SMTP email sending with mocked SMTP."""

    def _make_smtp_service(self):
        """Create an EmailService configured for SMTP."""
        env = {k: v for k, v in os.environ.items() if k != "SENDGRID_API_KEY"}
        env["SMTP_USER"] = "sender@test.com"
        env["SMTP_PASSWORD"] = "password123"
        env["SMTP_HOST"] = "smtp.test.com"
        env["SMTP_PORT"] = "587"
        with patch.dict(os.environ, env, clear=True):
            return EmailService()

    @patch("smtplib.SMTP")
    def test_smtp_send_success(self, mock_smtp_class):
        """SMTP send should return True on success."""
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        service = self._make_smtp_service()
        result = service._send_via_smtp(
            to_email="user@example.com",
            subject="Test",
            html_content="<p>Hello</p>",
        )
        assert result is True

    @patch("smtplib.SMTP")
    def test_smtp_connection_error_returns_false(self, mock_smtp_class):
        """SMTP send should return False on connection error."""
        mock_smtp_class.side_effect = ConnectionError("Connection refused")

        service = self._make_smtp_service()
        result = service._send_via_smtp(
            to_email="user@example.com",
            subject="Test",
            html_content="<p>Hello</p>",
        )
        assert result is False


class TestPasswordResetEmail:
    """Tests for send_password_reset_email template."""

    @patch("rivaflow.core.services.email_service.EmailService.send_email")
    def test_password_reset_calls_send_email(self, mock_send):
        """Password reset should call send_email with correct subject."""
        mock_send.return_value = True
        with patch.dict(os.environ, {"SENDGRID_API_KEY": "SG.fake"}, clear=False):
            service = EmailService()

        result = service.send_password_reset_email(
            to_email="user@example.com",
            reset_token="reset-token-abc",
            user_name="Alice",
        )
        assert result is True
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args
        assert call_kwargs[1]["subject"] == "Reset Your RivaFlow Password"
        assert "reset-token-abc" in call_kwargs[1]["html_content"]
        assert "Hi Alice," in call_kwargs[1]["html_content"]

    @patch("rivaflow.core.services.email_service.EmailService.send_email")
    def test_password_reset_without_user_name(self, mock_send):
        """Password reset without user_name should use generic greeting."""
        mock_send.return_value = True
        with patch.dict(os.environ, {"SENDGRID_API_KEY": "SG.fake"}, clear=False):
            service = EmailService()

        service.send_password_reset_email(
            to_email="user@example.com",
            reset_token="tok",
        )
        call_kwargs = mock_send.call_args
        assert "Hi," in call_kwargs[1]["html_content"]


class TestPasswordChangedEmail:
    """Tests for send_password_changed_confirmation."""

    @patch("rivaflow.core.services.email_service.EmailService.send_email")
    def test_password_changed_calls_send_email(self, mock_send):
        """Confirmation email should be sent with correct subject."""
        mock_send.return_value = True
        with patch.dict(os.environ, {"SENDGRID_API_KEY": "SG.fake"}, clear=False):
            service = EmailService()

        result = service.send_password_changed_confirmation(
            to_email="user@example.com",
            user_name="Bob",
        )
        assert result is True
        call_kwargs = mock_send.call_args
        assert call_kwargs[1]["subject"] == "Your RivaFlow Password Was Changed"
        assert "Hi Bob," in call_kwargs[1]["html_content"]


class TestWelcomeEmail:
    """Tests for send_welcome_email."""

    @patch("rivaflow.core.services.email_service.EmailService.send_email")
    def test_welcome_email_with_name(self, mock_send):
        """Welcome email should include first name."""
        mock_send.return_value = True
        with patch.dict(os.environ, {"SENDGRID_API_KEY": "SG.fake"}, clear=False):
            service = EmailService()

        result = service.send_welcome_email(
            email="new@example.com", first_name="Charlie"
        )
        assert result is True
        call_kwargs = mock_send.call_args
        assert "Hey Charlie," in call_kwargs[1]["html_content"]

    @patch("rivaflow.core.services.email_service.EmailService.send_email")
    def test_welcome_email_without_name(self, mock_send):
        """Welcome email without name should use generic greeting."""
        mock_send.return_value = True
        with patch.dict(os.environ, {"SENDGRID_API_KEY": "SG.fake"}, clear=False):
            service = EmailService()

        service.send_welcome_email(email="new@example.com")
        call_kwargs = mock_send.call_args
        assert "Hey there," in call_kwargs[1]["html_content"]


class TestWaitlistInviteEmail:
    """Tests for send_waitlist_invite_email."""

    @patch("rivaflow.core.services.email_service.EmailService.send_email")
    def test_waitlist_invite_includes_token(self, mock_send):
        """Waitlist invite should include the invite token in the link."""
        mock_send.return_value = True
        with patch.dict(os.environ, {"SENDGRID_API_KEY": "SG.fake"}, clear=False):
            service = EmailService()

        service.send_waitlist_invite_email(
            email="invited@example.com",
            first_name="Dana",
            invite_token="inv-token-xyz",
        )
        call_kwargs = mock_send.call_args
        assert "inv-token-xyz" in call_kwargs[1]["html_content"]
        assert "Hi Dana," in call_kwargs[1]["html_content"]


class TestDripEmails:
    """Tests for drip email templates."""

    @patch("rivaflow.core.services.email_service.EmailService.send_email")
    def test_drip_day1_subject(self, mock_send):
        """Day 1 drip should have correct subject."""
        mock_send.return_value = True
        with patch.dict(os.environ, {"SENDGRID_API_KEY": "SG.fake"}, clear=False):
            service = EmailService()

        service.send_drip_day1(email="user@example.com", first_name="Eve")
        call_kwargs = mock_send.call_args
        assert "Day 1" in call_kwargs[1]["subject"]

    @patch("rivaflow.core.services.email_service.EmailService.send_email")
    def test_drip_day3_subject(self, mock_send):
        """Day 3 drip should have correct subject."""
        mock_send.return_value = True
        with patch.dict(os.environ, {"SENDGRID_API_KEY": "SG.fake"}, clear=False):
            service = EmailService()

        service.send_drip_day3(email="user@example.com")
        call_kwargs = mock_send.call_args
        assert "Day 3" in call_kwargs[1]["subject"]

    @patch("rivaflow.core.services.email_service.EmailService.send_email")
    def test_drip_day5_subject(self, mock_send):
        """Day 5 drip should have correct subject."""
        mock_send.return_value = True
        with patch.dict(os.environ, {"SENDGRID_API_KEY": "SG.fake"}, clear=False):
            service = EmailService()

        service.send_drip_day5(email="user@example.com", first_name="Frank")
        call_kwargs = mock_send.call_args
        assert "Day 5" in call_kwargs[1]["subject"]
        assert "Hey Frank," in call_kwargs[1]["html_content"]


class TestFeedbackNotification:
    """Tests for send_feedback_notification."""

    @patch("rivaflow.core.services.email_service.EmailService.send_email")
    def test_feedback_notification_no_admin_emails(self, mock_send):
        """Should return False when ADMIN_EMAILS is not set."""
        with patch.dict(os.environ, {"ADMIN_EMAILS": ""}, clear=False):
            with patch.dict(os.environ, {"SENDGRID_API_KEY": "SG.fake"}, clear=False):
                service = EmailService()

            result = service.send_feedback_notification(
                feedback_id=1,
                category="bug",
                subject="Broken button",
                message="The submit button does not work",
                user_email="reporter@example.com",
                user_name="Reporter",
            )
            assert result is False
            mock_send.assert_not_called()

    @patch("rivaflow.core.services.email_service.EmailService.send_email")
    def test_feedback_notification_sends_to_admins(self, mock_send):
        """Should send to all configured admin emails."""
        mock_send.return_value = True
        with patch.dict(
            os.environ,
            {
                "ADMIN_EMAILS": "admin1@test.com,admin2@test.com",
                "SENDGRID_API_KEY": "SG.fake",
            },
            clear=False,
        ):
            service = EmailService()
            result = service.send_feedback_notification(
                feedback_id=42,
                category="feature",
                subject="Add dark mode",
                message="Please add dark mode",
                user_email="user@example.com",
                user_name="User",
            )
        assert result is True
        assert mock_send.call_count == 2


class TestCoachSettingsReminder:
    """Tests for send_coach_settings_reminder."""

    @patch("rivaflow.core.services.email_service.EmailService.send_email")
    def test_coach_settings_reminder(self, mock_send):
        """Coach settings reminder should send with correct subject."""
        mock_send.return_value = True
        with patch.dict(os.environ, {"SENDGRID_API_KEY": "SG.fake"}, clear=False):
            service = EmailService()

        result = service.send_coach_settings_reminder(
            email="user@example.com", first_name="Grace"
        )
        assert result is True
        call_kwargs = mock_send.call_args
        assert "Coach Settings" in call_kwargs[1]["subject"]
        assert "Hey Grace," in call_kwargs[1]["html_content"]
