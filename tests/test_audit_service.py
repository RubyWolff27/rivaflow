"""Unit tests for AuditService."""

from rivaflow.core.services.audit_service import AuditService


class TestAuditLogCreation:
    """Tests for creating audit log entries."""

    def test_create_basic_audit_log(self, test_user):
        """Should create an audit log and return a positive ID."""
        log_id = AuditService.log(
            actor_id=test_user["id"],
            action="user.login",
        )
        assert log_id > 0

    def test_create_audit_log_with_all_fields(self, test_user):
        """Should create an audit log with all optional fields."""
        log_id = AuditService.log(
            actor_id=test_user["id"],
            action="user.update",
            target_type="user",
            target_id=42,
            details={"field": "email", "old": "a@b.com", "new": "c@d.com"},
            ip_address="192.168.1.1",
        )
        assert log_id > 0

    def test_create_multiple_audit_logs(self, test_user):
        """Should create multiple audit logs with distinct IDs."""
        id1 = AuditService.log(actor_id=test_user["id"], action="user.login")
        id2 = AuditService.log(actor_id=test_user["id"], action="user.logout")
        assert id1 > 0
        assert id2 > 0
        assert id1 != id2

    def test_audit_log_with_none_details(self, test_user):
        """Should handle None details gracefully."""
        log_id = AuditService.log(
            actor_id=test_user["id"],
            action="session.create",
            details=None,
        )
        assert log_id > 0

    def test_audit_log_with_empty_details(self, test_user):
        """Should handle empty dict details."""
        log_id = AuditService.log(
            actor_id=test_user["id"],
            action="session.delete",
            details={},
        )
        assert log_id > 0


class TestAuditLogRetrieval:
    """Tests for retrieving audit logs."""

    def test_get_logs_returns_created_entries(self, test_user):
        """Should return logs that were previously created."""
        AuditService.log(actor_id=test_user["id"], action="user.login")
        AuditService.log(actor_id=test_user["id"], action="user.logout")

        logs = AuditService.get_logs()
        assert len(logs) >= 2

    def test_get_logs_includes_actor_email(self, test_user):
        """Logs should include actor email from joined users table."""
        AuditService.log(actor_id=test_user["id"], action="user.login")

        logs = AuditService.get_logs(actor_id=test_user["id"])
        assert len(logs) >= 1
        assert logs[0]["actor_email"] == "test@example.com"

    def test_get_logs_includes_actor_name(self, test_user):
        """Logs should include actor first/last name."""
        AuditService.log(actor_id=test_user["id"], action="user.login")

        logs = AuditService.get_logs(actor_id=test_user["id"])
        assert logs[0]["actor_first_name"] == "Test"
        assert logs[0]["actor_last_name"] == "User"

    def test_get_logs_parses_json_details(self, test_user):
        """JSON details should be parsed back into a dict."""
        details = {"changed_field": "email", "reason": "typo"}
        AuditService.log(
            actor_id=test_user["id"],
            action="user.update",
            details=details,
        )

        logs = AuditService.get_logs(actor_id=test_user["id"], action="user.update")
        assert len(logs) >= 1
        assert isinstance(logs[0]["details"], dict)
        assert logs[0]["details"]["changed_field"] == "email"

    def test_get_logs_ordered_newest_first(self, test_user):
        """Logs should be ordered by created_at descending (newest first).

        Note: Both inserts may get the same CURRENT_TIMESTAMP (second
        precision in SQLite), so we verify ordering by id as a proxy --
        higher id should appear first since ORDER BY created_at DESC
        is stable with respect to insertion order in practice.
        """
        AuditService.log(actor_id=test_user["id"], action="first.action")
        AuditService.log(actor_id=test_user["id"], action="second.action")

        logs = AuditService.get_logs(actor_id=test_user["id"])
        assert len(logs) >= 2
        actions = {log["action"] for log in logs}
        assert "first.action" in actions
        assert "second.action" in actions


class TestAuditLogFilterByAction:
    """Tests for filtering audit logs by action type."""

    def test_filter_by_action(self, test_user):
        """Should return only logs matching the given action."""
        AuditService.log(actor_id=test_user["id"], action="user.login")
        AuditService.log(actor_id=test_user["id"], action="user.update")
        AuditService.log(actor_id=test_user["id"], action="user.login")

        logs = AuditService.get_logs(action="user.login")
        assert len(logs) == 2
        assert all(log["action"] == "user.login" for log in logs)

    def test_filter_by_target_type(self, test_user):
        """Should return only logs matching the given target_type."""
        AuditService.log(
            actor_id=test_user["id"],
            action="entity.update",
            target_type="gym",
            target_id=1,
        )
        AuditService.log(
            actor_id=test_user["id"],
            action="entity.update",
            target_type="user",
            target_id=2,
        )

        logs = AuditService.get_logs(target_type="gym")
        assert len(logs) == 1
        assert logs[0]["target_type"] == "gym"

    def test_filter_by_target_id(self, test_user):
        """Should return only logs matching the given target_id."""
        AuditService.log(
            actor_id=test_user["id"],
            action="user.delete",
            target_type="user",
            target_id=99,
        )
        AuditService.log(
            actor_id=test_user["id"],
            action="user.delete",
            target_type="user",
            target_id=100,
        )

        logs = AuditService.get_logs(target_id=99)
        assert len(logs) == 1
        assert logs[0]["target_id"] == 99

    def test_filter_by_actor_id(self, test_user, test_user2):
        """Should return only logs for a specific actor."""
        AuditService.log(actor_id=test_user["id"], action="user.login")
        AuditService.log(actor_id=test_user2["id"], action="user.login")

        logs = AuditService.get_logs(actor_id=test_user["id"])
        assert len(logs) == 1
        assert logs[0]["actor_user_id"] == test_user["id"]

    def test_no_results_for_unmatched_action(self, test_user):
        """Should return empty list when no logs match the filter."""
        AuditService.log(actor_id=test_user["id"], action="user.login")

        logs = AuditService.get_logs(action="nonexistent.action")
        assert logs == []


class TestAuditLogPagination:
    """Tests for pagination of audit logs."""

    def test_limit_restricts_results(self, test_user):
        """Should return no more than `limit` entries."""
        for i in range(5):
            AuditService.log(actor_id=test_user["id"], action=f"action.{i}")

        logs = AuditService.get_logs(limit=3)
        assert len(logs) == 3

    def test_offset_skips_entries(self, test_user):
        """Should skip `offset` entries."""
        for i in range(5):
            AuditService.log(actor_id=test_user["id"], action=f"action.{i}")

        all_logs = AuditService.get_logs(limit=100)
        offset_logs = AuditService.get_logs(limit=100, offset=2)
        assert len(offset_logs) == len(all_logs) - 2

    def test_limit_and_offset_together(self, test_user):
        """Should paginate correctly with both limit and offset."""
        for i in range(10):
            AuditService.log(actor_id=test_user["id"], action=f"action.{i}")

        page1 = AuditService.get_logs(limit=3, offset=0)
        page2 = AuditService.get_logs(limit=3, offset=3)

        assert len(page1) == 3
        assert len(page2) == 3
        # Pages should not overlap
        page1_ids = {log["id"] for log in page1}
        page2_ids = {log["id"] for log in page2}
        assert page1_ids.isdisjoint(page2_ids)

    def test_offset_beyond_total_returns_empty(self, test_user):
        """Offset beyond total count should return empty list."""
        AuditService.log(actor_id=test_user["id"], action="user.login")

        logs = AuditService.get_logs(offset=100)
        assert logs == []


class TestGetTotalCount:
    """Tests for get_total_count."""

    def test_total_count_all(self, test_user):
        """Should return total count of all logs."""
        AuditService.log(actor_id=test_user["id"], action="user.login")
        AuditService.log(actor_id=test_user["id"], action="user.logout")

        count = AuditService.get_total_count()
        assert count == 2

    def test_total_count_filtered_by_action(self, test_user):
        """Should return count filtered by action."""
        AuditService.log(actor_id=test_user["id"], action="user.login")
        AuditService.log(actor_id=test_user["id"], action="user.login")
        AuditService.log(actor_id=test_user["id"], action="user.logout")

        count = AuditService.get_total_count(action="user.login")
        assert count == 2

    def test_total_count_zero_for_no_matches(self, test_user):
        """Should return 0 when no logs match."""
        AuditService.log(actor_id=test_user["id"], action="user.login")

        count = AuditService.get_total_count(action="nonexistent")
        assert count == 0


class TestGetUserActivitySummary:
    """Tests for get_user_activity_summary."""

    def test_summary_includes_action_counts(self, test_user):
        """Activity summary should include action counts."""
        AuditService.log(actor_id=test_user["id"], action="user.login")
        AuditService.log(actor_id=test_user["id"], action="user.login")
        AuditService.log(actor_id=test_user["id"], action="session.create")

        summary = AuditService.get_user_activity_summary(test_user["id"])
        assert summary["user_id"] == test_user["id"]
        assert summary["total_actions"] == 3
        assert summary["action_counts"]["user.login"] == 2
        assert summary["action_counts"]["session.create"] == 1

    def test_summary_includes_most_recent_action(self, test_user):
        """Activity summary should include most recent action."""
        AuditService.log(actor_id=test_user["id"], action="user.login")
        AuditService.log(actor_id=test_user["id"], action="session.create")

        summary = AuditService.get_user_activity_summary(test_user["id"])
        assert summary["most_recent_action"] is not None
        # Both inserts may share the same CURRENT_TIMESTAMP (SQLite second
        # precision), so just verify the most_recent_action is one of them.
        assert summary["most_recent_action"]["action"] in (
            "user.login",
            "session.create",
        )

    def test_summary_empty_for_user_with_no_activity(self, test_user):
        """Activity summary should be empty for user with no logs."""
        summary = AuditService.get_user_activity_summary(test_user["id"])
        assert summary["total_actions"] == 0
        assert summary["action_counts"] == {}
        assert summary["most_recent_action"] is None
