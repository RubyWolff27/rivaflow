"""Database performance tests with large datasets."""

import os
import time
from datetime import date, timedelta

import pytest

from rivaflow.core.services.analytics_service import AnalyticsService
from rivaflow.db.database import convert_query, get_connection
from rivaflow.db.repositories.session_repo import SessionRepository

# Set test environment
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-performance-tests-minimum-32-chars")
os.environ.setdefault("ENV", "test")


class TestDatabasePerformance:
    """Test database performance with large datasets."""

    @pytest.fixture(scope="class")
    def large_dataset(self):
        """Create a large dataset of 10,000+ sessions for performance testing."""
        user_id = 1  # Test user
        repo = SessionRepository()

        sessions_created = []
        start_date = date.today() - timedelta(days=730)  # 2 years of data

        print("\nGenerating 10,000 test sessions...")
        start_time = time.time()

        for i in range(10000):
            session_date = start_date + timedelta(days=i % 730)
            class_type = ["gi", "no-gi", "s&c", "mobility"][i % 4]

            session_id = repo.create(
                user_id=user_id,
                session_date=session_date,
                class_type=class_type,
                gym_name="Test Academy",
                duration_mins=60 + (i % 60),
                intensity=3 + (i % 3),
                rolls=5 + (i % 10) if class_type in ["gi", "no-gi"] else 0,
                submissions_for=i % 5,
                submissions_against=i % 3,
            )
            sessions_created.append(session_id)

        end_time = time.time()
        print(f"Created 10,000 sessions in {end_time - start_time:.2f}s")

        yield {"user_id": user_id, "session_ids": sessions_created}

        # Cleanup
        print("\nCleaning up test sessions...")
        with get_connection() as conn:
            cursor = conn.cursor()
            for session_id in sessions_created:
                cursor.execute(convert_query("DELETE FROM sessions WHERE id = ?"), (session_id,))

    def test_list_sessions_performance(self, large_dataset):
        """Test performance of listing sessions with large dataset."""
        repo = SessionRepository()
        user_id = large_dataset["user_id"]

        # Test 1: List all sessions
        start_time = time.time()
        all_sessions = repo.list_by_user(user_id)
        end_time = time.time()

        query_time = end_time - start_time
        print(f"\nList all 10,000 sessions: {query_time:.3f}s")

        assert len(all_sessions) >= 10000
        assert query_time < 2.0, f"Query took {query_time:.3f}s, should be under 2s"

    def test_date_range_query_performance(self, large_dataset):
        """Test performance of date range queries."""
        repo = SessionRepository()
        user_id = large_dataset["user_id"]

        # Test 2: Date range query (30 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        start_time = time.time()
        repo.list_by_user(user_id, start_date=start_date, end_date=end_date)
        end_time = time.time()

        query_time = end_time - start_time
        print(f"\nDate range query (30 days): {query_time:.3f}s")

        assert query_time < 0.5, f"Date range query took {query_time:.3f}s, should be under 0.5s"

    def test_aggregation_query_performance(self, large_dataset):
        """Test performance of aggregation queries."""
        user_id = large_dataset["user_id"]

        # Test 3: Aggregation query (total stats)
        start_time = time.time()

        with get_connection() as conn:
            cursor = conn.cursor()

            # Total hours
            cursor.execute(
                convert_query("SELECT SUM(duration_mins) FROM sessions WHERE user_id = ?"),
                (user_id,),
            )
            total_mins = cursor.fetchone()[0]

            # Total sessions
            cursor.execute(
                convert_query("SELECT COUNT(*) FROM sessions WHERE user_id = ?"),
                (user_id,),
            )
            total_sessions = cursor.fetchone()[0]

            # Submissions
            cursor.execute(
                convert_query(
                    """
                    SELECT SUM(submissions_for), SUM(submissions_against)
                    FROM sessions WHERE user_id = ?
                """
                ),
                (user_id,),
            )
            subs_for, subs_against = cursor.fetchone()

        end_time = time.time()

        query_time = end_time - start_time
        print(f"\nAggregation queries (4 stats): {query_time:.3f}s")
        print(f"  Total sessions: {total_sessions}")
        print(f"  Total hours: {total_mins / 60:.1f}")

        assert query_time < 0.3, f"Aggregation queries took {query_time:.3f}s, should be under 0.3s"

    def test_analytics_service_performance(self, large_dataset):
        """Test analytics service performance with large dataset."""
        user_id = large_dataset["user_id"]
        analytics_service = AnalyticsService()

        # Test 4: Analytics overview
        start_time = time.time()
        overview = analytics_service.performance.get_performance_overview(user_id)
        end_time = time.time()

        query_time = end_time - start_time
        print(f"\nAnalytics overview: {query_time:.3f}s")

        assert "total_sessions" in overview
        assert query_time < 3.0, f"Analytics took {query_time:.3f}s, should be under 3s"

    def test_pagination_performance(self, large_dataset):
        """Test pagination performance."""
        repo = SessionRepository()
        user_id = large_dataset["user_id"]

        # Test 5: Paginated queries
        page_size = 20
        num_pages = 5

        total_time = 0
        for page in range(num_pages):
            start_time = time.time()
            repo.list_by_user(user_id, limit=page_size, offset=page * page_size)
            end_time = time.time()

            page_time = end_time - start_time
            total_time += page_time

        avg_page_time = total_time / num_pages
        print(f"\nPagination ({num_pages} pages of {page_size}): avg {avg_page_time:.3f}s per page")

        assert (
            avg_page_time < 0.1
        ), f"Pagination took {avg_page_time:.3f}s per page, should be under 0.1s"

    def test_index_effectiveness(self, large_dataset):
        """Test that database indexes are being used effectively."""
        user_id = large_dataset["user_id"]

        with get_connection() as conn:
            cursor = conn.cursor()

            # Enable query plan analysis (SQLite)
            cursor.execute(
                "EXPLAIN QUERY PLAN SELECT * FROM sessions WHERE user_id = ?",
                (user_id,),
            )
            plan = cursor.fetchall()

            print("\nQuery plan for user_id filter:")
            for row in plan:
                print(f"  {row}")

            # Check that an index is being used
            plan_str = str(plan).lower()
            # Should contain "index" or "idx" if index is being used
            assert "index" in plan_str or "idx" in plan_str, "Query should use an index on user_id"


class TestQueryOptimization:
    """Test query optimization and N+1 problems."""

    def test_avoid_n_plus_1_partners(self):
        """Verify that partner queries don't cause N+1 problems."""
        user_id = 1
        repo = SessionRepository()

        # Create 100 sessions with partners
        session_ids = []
        for i in range(100):
            session_id = repo.create(
                user_id=user_id,
                session_date=date.today() - timedelta(days=i),
                class_type="gi",
                gym_name="Test Academy",
                duration_mins=60,
                intensity=4,
                rolls=5,
                partners=["Partner A", "Partner B", "Partner C"],
            )
            session_ids.append(session_id)

        try:
            # Query all sessions and extract partners
            start_time = time.time()
            sessions = repo.list_by_user(user_id)

            unique_partners = set()
            for session in sessions:
                if session.get("partners"):
                    # Partners should be included in session data, not require separate query
                    unique_partners.update(session["partners"])

            end_time = time.time()

            query_time = end_time - start_time
            print(f"\nExtract partners from 100 sessions: {query_time:.3f}s")

            # Should complete quickly without N+1 queries
            assert (
                query_time < 0.5
            ), f"Partner extraction took {query_time:.3f}s, possible N+1 problem"

        finally:
            # Cleanup
            with get_connection() as conn:
                cursor = conn.cursor()
                for session_id in session_ids:
                    cursor.execute(
                        convert_query("DELETE FROM sessions WHERE id = ?"),
                        (session_id,),
                    )


class TestMemoryUsage:
    """Test memory usage with large datasets."""

    def test_streaming_large_results(self):
        """Test that large result sets don't cause excessive memory usage."""
        import gc

        import psutil

        # Force garbage collection before test
        gc.collect()

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        user_id = 1
        repo = SessionRepository()

        # Create 5000 sessions
        session_ids = []
        for i in range(5000):
            session_id = repo.create(
                user_id=user_id,
                session_date=date.today() - timedelta(days=i % 365),
                class_type="gi",
                gym_name="Test Academy",
                duration_mins=60,
                intensity=4,
                rolls=5,
            )
            session_ids.append(session_id)

        try:
            # Query all sessions
            sessions = repo.list_by_user(user_id)

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            print(
                f"\nMemory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{memory_increase:.1f}MB)"
            )
            print(f"Sessions loaded: {len(sessions)}")
            print(f"Memory per session: {(memory_increase * 1024) / len(sessions):.2f}KB")

            # Should not use excessive memory (< 200MB increase for 5000 sessions)
            assert memory_increase < 200, f"Memory increase of {memory_increase:.1f}MB is excessive"

        finally:
            # Cleanup
            with get_connection() as conn:
                cursor = conn.cursor()
                for session_id in session_ids:
                    cursor.execute(
                        convert_query("DELETE FROM sessions WHERE id = ?"),
                        (session_id,),
                    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
