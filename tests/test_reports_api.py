"""Integration tests for analytics/reports API endpoints."""

from datetime import date, timedelta


class TestAnalyticsAPI:
    """Test suite for analytics API endpoints."""

    def test_performance_overview_empty_data(self, client, test_user, auth_headers):
        """Test performance overview with no sessions."""
        response = client.get(
            "/api/v1/analytics/performance-overview", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify empty data structure
        assert data["summary"]["total_sessions"] == 0
        assert data["summary"]["total_submissions_for"] == 0
        assert data["summary"]["avg_intensity"] == 0.0
        assert data["deltas"]["sessions"] == 0
        assert len(data["daily_timeseries"]["sessions"]) > 0  # Should have dates

    def test_performance_overview_with_date_range(
        self, client, test_user, auth_headers, session_factory
    ):
        """Test performance overview with specific date range."""
        # Create sessions
        today = date.today()
        session_factory(
            session_date=today,
            intensity=4,
            rolls=5,
            submissions_for=3,
            submissions_against=1,
        )
        session_factory(
            session_date=today - timedelta(days=1),
            intensity=3,
            rolls=4,
            submissions_for=2,
            submissions_against=2,
        )

        # Test with date range
        start_date = (today - timedelta(days=7)).isoformat()
        end_date = today.isoformat()

        response = client.get(
            f"/api/v1/analytics/performance-overview?start_date={start_date}&end_date={end_date}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify data
        assert data["summary"]["total_sessions"] == 2
        assert data["summary"]["total_submissions_for"] == 5
        assert data["summary"]["total_rolls"] == 9
        assert data["summary"]["avg_intensity"] == 3.5

    def test_performance_overview_single_session(
        self, client, test_user, auth_headers, session_factory
    ):
        """Test edge case with only one session."""
        today = date.today()
        session_factory(
            session_date=today,
            intensity=5,
            rolls=3,
            submissions_for=2,
            submissions_against=0,
        )

        start_date = (today - timedelta(days=7)).isoformat()
        end_date = (today + timedelta(days=1)).isoformat()

        response = client.get(
            f"/api/v1/analytics/performance-overview?start_date={start_date}&end_date={end_date}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify single session handling
        assert data["summary"]["total_sessions"] == 1
        assert data["summary"]["avg_intensity"] == 5.0
        assert data["daily_timeseries"] is not None

    def test_performance_overview_division_by_zero(
        self, client, test_user, auth_headers, session_factory
    ):
        """Test division by zero protection in calculations."""
        today = date.today()
        # Session with zero submissions against
        session_factory(
            session_date=today,
            intensity=4,
            rolls=0,  # Zero rolls
            submissions_for=0,
            submissions_against=0,
        )

        start_date = (today - timedelta(days=7)).isoformat()
        end_date = (today + timedelta(days=1)).isoformat()

        response = client.get(
            f"/api/v1/analytics/performance-overview?start_date={start_date}&end_date={end_date}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should not crash with division by zero
        assert data["summary"]["total_sessions"] == 1
        assert "daily_timeseries" in data

    def test_partner_stats_empty_data(self, client, test_user, auth_headers):
        """Test partner stats with no data."""
        response = client.get("/api/v1/analytics/partners/stats", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify empty partner data
        assert data["diversity_metrics"]["active_partners"] == 0
        assert data["summary"]["total_rolls"] == 0
        assert len(data["top_partners"]) == 0

    def test_partner_stats_with_data(
        self, client, test_user, auth_headers, session_factory, friend_repo
    ):
        """Test partner stats with training partner data."""
        # Create a training partner
        friend_repo.create(
            user_id=test_user["id"],
            name="John Doe",
            friend_type="training-partner",
            belt_rank="blue",
            belt_stripes=2,
        )

        # Create session (note: session factory doesn't link rolls, this is basic test)
        session_factory(session_date=date.today(), intensity=4, rolls=5)

        response = client.get("/api/v1/analytics/partners/stats", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify partner data structure
        assert "diversity_metrics" in data
        assert "top_partners" in data
        assert "summary" in data

    def test_technique_breakdown_empty_data(self, client, test_user, auth_headers):
        """Test technique breakdown with no data."""
        response = client.get(
            "/api/v1/analytics/techniques/breakdown", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify empty technique data
        assert data["summary"]["total_unique_techniques_used"] == 0
        assert len(data["category_breakdown"]) == 0
        assert len(data["gi_top_techniques"]) == 0
        assert len(data["nogi_top_techniques"]) == 0

    def test_technique_breakdown_with_sessions(
        self, client, test_user, auth_headers, session_factory
    ):
        """Test technique breakdown with session data."""
        # Create gi and no-gi sessions
        session_factory(
            session_date=date.today(), class_type="gi", intensity=4, rolls=5
        )
        session_factory(
            session_date=date.today() - timedelta(days=1),
            class_type="no-gi",
            intensity=3,
            rolls=4,
        )

        response = client.get(
            "/api/v1/analytics/techniques/breakdown", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify structure (may be empty if no roll details)
        assert "summary" in data
        assert "category_breakdown" in data
        assert "gi_top_techniques" in data
        assert "nogi_top_techniques" in data
        assert "stale_techniques" in data

    def test_date_range_validation(self, client, test_user, auth_headers):
        """Test various date range scenarios."""
        # Test last 7 days (default behavior)
        response = client.get(
            "/api/v1/analytics/performance-overview", headers=auth_headers
        )
        assert response.status_code == 200

        # Test last 30 days
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()

        response = client.get(
            f"/api/v1/analytics/performance-overview?start_date={start_date}&end_date={end_date}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Test all time (1 year back)
        start_date = (date.today() - timedelta(days=365)).isoformat()

        response = client.get(
            f"/api/v1/analytics/performance-overview?start_date={start_date}&end_date={end_date}",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_date_range_no_data_in_range(
        self, client, test_user, auth_headers, session_factory
    ):
        """Test date range with no data in selected range."""
        # Create session in the past
        old_date = date.today() - timedelta(days=100)
        session_factory(session_date=old_date, intensity=4, rolls=5)

        # Query recent range (no data)
        start_date = (date.today() - timedelta(days=7)).isoformat()
        end_date = date.today().isoformat()

        response = client.get(
            f"/api/v1/analytics/performance-overview?start_date={start_date}&end_date={end_date}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return empty data for this range
        assert data["summary"]["total_sessions"] == 0

    def test_null_value_handling(
        self, client, test_user, auth_headers, session_factory
    ):
        """Test handling of null/None values in session data."""
        # Create session with minimal data
        session_factory(
            session_date=date.today(),
            class_type="gi",
            duration_mins=60,
            intensity=3,
            rolls=0,  # Edge case: zero rolls
            submissions_for=0,
            submissions_against=0,
        )

        response = client.get(
            "/api/v1/analytics/performance-overview", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should handle zeros gracefully
        assert data["summary"]["total_rolls"] == 0
        assert data["summary"]["total_submissions_for"] == 0

    def test_consistency_metrics(
        self, client, test_user, auth_headers, session_factory
    ):
        """Test consistency analytics endpoint."""
        # Create multiple sessions
        for i in range(5):
            session_factory(
                session_date=date.today() - timedelta(days=i), intensity=4, rolls=5
            )

        response = client.get(
            "/api/v1/analytics/consistency/metrics", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify consistency data structure
        assert "weekly_volume" in data
        assert "class_type_distribution" in data
        assert "gym_breakdown" in data
        assert "streaks" in data

    def test_unauthorized_access(self, client):
        """Test that endpoints require authentication."""
        response = client.get("/api/v1/analytics/performance-overview")
        assert response.status_code == 401

    def test_milestones_endpoint(self, client, test_user, auth_headers):
        """Test milestones endpoint."""
        response = client.get("/api/v1/analytics/milestones", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify milestone data structure
        assert "belt_progression" in data
        assert "personal_records" in data
        assert "rolling_totals" in data


class TestAnalyticsEdgeCases:
    """Test edge cases in analytics calculations."""

    def test_intensity_calculation_with_nulls(
        self, client, test_user, auth_headers, session_factory
    ):
        """Test average intensity calculation with varying intensities."""
        today = date.today()
        session_factory(session_date=today, intensity=5, rolls=3)
        session_factory(session_date=today - timedelta(days=1), intensity=1, rolls=2)
        session_factory(session_date=today - timedelta(days=2), intensity=3, rolls=4)

        start_date = (today - timedelta(days=7)).isoformat()
        end_date = (today + timedelta(days=1)).isoformat()

        response = client.get(
            f"/api/v1/analytics/performance-overview?start_date={start_date}&end_date={end_date}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Average should be (5 + 1 + 3) / 3 = 3.0
        assert data["summary"]["avg_intensity"] == 3.0

    def test_timeseries_completeness(
        self, client, test_user, auth_headers, session_factory
    ):
        """Test that timeseries includes all days in range, even with no data."""
        # Create session only on one day
        session_factory(session_date=date.today(), intensity=4, rolls=5)

        # Query 7-day range
        start_date = (date.today() - timedelta(days=6)).isoformat()
        end_date = date.today().isoformat()

        response = client.get(
            f"/api/v1/analytics/performance-overview?start_date={start_date}&end_date={end_date}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should have 7 data points (one per day)
        assert len(data["daily_timeseries"]["sessions"]) == 7

        # Most days should be 0, except today
        assert sum(data["daily_timeseries"]["sessions"]) == 1

    def test_delta_calculation_no_previous_data(
        self, client, test_user, auth_headers, session_factory
    ):
        """Test delta calculation when there's no previous period data."""
        today = date.today()
        # Only create session today
        session_factory(session_date=today, intensity=4, rolls=5, submissions_for=2)

        start_date = (today - timedelta(days=7)).isoformat()
        end_date = (today + timedelta(days=1)).isoformat()

        response = client.get(
            f"/api/v1/analytics/performance-overview?start_date={start_date}&end_date={end_date}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Deltas should reflect change from 0
        assert data["deltas"]["sessions"] > 0
        assert data["deltas"]["submissions"] > 0
