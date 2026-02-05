"""API load testing with concurrent requests."""

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

import pytest

from rivaflow.db.database import convert_query, get_connection

# Set test environment
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-load-tests-minimum-32-chars")
os.environ.setdefault("ENV", "test")


class TestAPILoadPerformance:
    """Test API performance under concurrent load."""

    @pytest.fixture(scope="class")
    def test_user_token(self):
        """Create a test user and get auth token."""
        from rivaflow.core.services.auth_service import AuthService
        from rivaflow.db.repositories.user_repo import UserRepository

        # Create test user
        auth_service = AuthService()
        user_repo = UserRepository()

        # Clean up any existing test user
        existing = user_repo.get_by_email("loadtest@rivaflow.com")
        if existing:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    convert_query("DELETE FROM users WHERE email = ?"),
                    ("loadtest@rivaflow.com",),
                )

        # Register new test user
        result = auth_service.register(
            email="loadtest@rivaflow.com",
            password="TestPassword123!",
            first_name="Load",
            last_name="Test",
        )

        access_token = result["access_token"]
        user_id = result["user"]["id"]

        yield {"token": access_token, "user_id": user_id}

        # Cleanup
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("DELETE FROM users WHERE id = ?"), (user_id,))

    def test_concurrent_session_creation(self, test_user_token):
        """Test creating sessions with 100 concurrent requests."""
        from rivaflow.db.repositories.session_repo import SessionRepository

        user_id = test_user_token["user_id"]
        repo = SessionRepository()

        num_requests = 100
        session_ids = []

        def create_session(i):
            """Create a single session."""
            try:
                session_id = repo.create(
                    user_id=user_id,
                    session_date=date.today() - timedelta(days=i % 30),
                    class_type=["gi", "no-gi", "s&c"][i % 3],
                    gym_name="Test Academy",
                    duration_mins=60,
                    intensity=4,
                    rolls=5,
                )
                return {"success": True, "session_id": session_id}
            except Exception as e:
                return {"success": False, "error": str(e)}

        print(f"\nCreating {num_requests} sessions concurrently...")
        start_time = time.time()

        # Use ThreadPoolExecutor for concurrent execution
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(create_session, i) for i in range(num_requests)]

            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                if result["success"]:
                    session_ids.append(result["session_id"])

        end_time = time.time()
        total_time = end_time - start_time

        # Calculate statistics
        successful = sum(1 for r in results if r["success"])
        failed = sum(1 for r in results if not r["success"])
        throughput = successful / total_time

        print(f"Time: {total_time:.2f}s")
        print(f"Successful: {successful}/{num_requests}")
        print(f"Failed: {failed}")
        print(f"Throughput: {throughput:.1f} req/s")

        # Assertions
        assert successful == num_requests, f"Only {successful}/{num_requests} requests succeeded"
        assert total_time < 10.0, f"Took {total_time:.2f}s, should complete in under 10s"
        assert throughput > 10, f"Throughput of {throughput:.1f} req/s is too low"

        # Cleanup
        try:
            from rivaflow.db.database import convert_query, get_connection

            with get_connection() as conn:
                cursor = conn.cursor()
                for session_id in session_ids:
                    cursor.execute(
                        convert_query("DELETE FROM sessions WHERE id = ?"),
                        (session_id,),
                    )
        except Exception:
            pass

    def test_concurrent_read_operations(self, test_user_token):
        """Test reading sessions with 100 concurrent requests."""
        from rivaflow.db.repositories.session_repo import SessionRepository

        user_id = test_user_token["user_id"]
        repo = SessionRepository()

        # Create some test sessions first
        session_ids = []
        for i in range(50):
            session_id = repo.create(
                user_id=user_id,
                session_date=date.today() - timedelta(days=i),
                class_type="gi",
                gym_name="Test Academy",
                duration_mins=60,
                intensity=4,
                rolls=5,
            )
            session_ids.append(session_id)

        try:
            num_requests = 100

            def read_sessions():
                """Read all sessions."""
                try:
                    sessions = repo.list_by_user(user_id)
                    return {"success": True, "count": len(sessions)}
                except Exception as e:
                    return {"success": False, "error": str(e)}

            print(f"\n{num_requests} concurrent read requests...")
            start_time = time.time()

            # Execute concurrent reads
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(read_sessions) for _ in range(num_requests)]
                results = [future.result() for future in as_completed(futures)]

            end_time = time.time()
            total_time = end_time - start_time

            successful = sum(1 for r in results if r["success"])
            throughput = successful / total_time

            print(f"Time: {total_time:.2f}s")
            print(f"Successful: {successful}/{num_requests}")
            print(f"Throughput: {throughput:.1f} req/s")

            # Read operations should be fast
            assert successful == num_requests
            assert total_time < 5.0, f"Reads took {total_time:.2f}s, should complete in under 5s"
            assert throughput > 20, f"Read throughput of {throughput:.1f} req/s is too low"

        finally:
            # Cleanup
            from rivaflow.db.database import convert_query, get_connection

            with get_connection() as conn:
                cursor = conn.cursor()
                for session_id in session_ids:
                    cursor.execute(
                        convert_query("DELETE FROM sessions WHERE id = ?"),
                        (session_id,),
                    )

    def test_mixed_workload_concurrent(self, test_user_token):
        """Test mixed read/write workload with concurrent requests."""
        from rivaflow.db.repositories.session_repo import SessionRepository

        user_id = test_user_token["user_id"]
        repo = SessionRepository()

        # Create initial sessions
        session_ids = []
        for i in range(20):
            session_id = repo.create(
                user_id=user_id,
                session_date=date.today() - timedelta(days=i),
                class_type="gi",
                gym_name="Test Academy",
                duration_mins=60,
                intensity=4,
                rolls=5,
            )
            session_ids.append(session_id)

        try:
            # Mixed workload: 60% reads, 30% writes, 10% updates
            num_requests = 100
            created_sessions = []

            def mixed_operation(i):
                """Execute a mixed operation."""
                try:
                    if i % 10 < 6:  # 60% reads
                        repo.list_by_user(user_id, limit=10)
                        return {"type": "read", "success": True}
                    elif i % 10 < 9:  # 30% writes
                        session_id = repo.create(
                            user_id=user_id,
                            session_date=date.today(),
                            class_type="gi",
                            gym_name="Test Academy",
                            duration_mins=60,
                            intensity=4,
                            rolls=5,
                        )
                        created_sessions.append(session_id)
                        return {
                            "type": "write",
                            "success": True,
                            "session_id": session_id,
                        }
                    else:  # 10% updates
                        if session_ids:
                            repo.update(
                                session_ids[i % len(session_ids)],
                                {"notes": f"Updated {i}"},
                            )
                        return {"type": "update", "success": True}
                except Exception as e:
                    return {"type": "error", "success": False, "error": str(e)}

            print(f"\n{num_requests} mixed operations (60% read, 30% write, 10% update)...")
            start_time = time.time()

            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(mixed_operation, i) for i in range(num_requests)]
                results = [future.result() for future in as_completed(futures)]

            end_time = time.time()
            total_time = end_time - start_time

            successful = sum(1 for r in results if r["success"])
            reads = sum(1 for r in results if r.get("type") == "read")
            writes = sum(1 for r in results if r.get("type") == "write")
            updates = sum(1 for r in results if r.get("type") == "update")
            throughput = successful / total_time

            print(f"Time: {total_time:.2f}s")
            print(f"Successful: {successful}/{num_requests}")
            print(f"  Reads: {reads}")
            print(f"  Writes: {writes}")
            print(f"  Updates: {updates}")
            print(f"Throughput: {throughput:.1f} req/s")

            assert successful >= num_requests * 0.95, "At least 95% should succeed"
            assert total_time < 15.0, f"Mixed workload took {total_time:.2f}s, should be under 15s"

            # Cleanup created sessions
            session_ids.extend(created_sessions)

        finally:
            # Cleanup all sessions
            from rivaflow.db.database import convert_query, get_connection

            with get_connection() as conn:
                cursor = conn.cursor()
                for session_id in session_ids:
                    cursor.execute(
                        convert_query("DELETE FROM sessions WHERE id = ?"),
                        (session_id,),
                    )


class TestAPIEndpointPerformance:
    """Test specific API endpoint performance."""

    def test_analytics_endpoint_performance(self):
        """Test analytics endpoint performance."""
        from rivaflow.core.services.analytics_service import AnalyticsService

        user_id = 1
        service = AnalyticsService()

        # Create 1000 test sessions
        from rivaflow.db.repositories.session_repo import SessionRepository

        repo = SessionRepository()

        session_ids = []
        for i in range(1000):
            session_id = repo.create(
                user_id=user_id,
                session_date=date.today() - timedelta(days=i % 90),
                class_type=["gi", "no-gi"][i % 2],
                gym_name="Test Academy",
                duration_mins=60,
                intensity=4,
                rolls=5,
                submissions_for=i % 3,
                submissions_against=i % 2,
            )
            session_ids.append(session_id)

        try:
            # Test analytics performance
            start_time = time.time()
            overview = service.performance.get_performance_overview(user_id)
            end_time = time.time()

            query_time = end_time - start_time
            print(f"\nAnalytics overview with 1000 sessions: {query_time:.3f}s")

            assert "total_sessions" in overview
            assert query_time < 2.0, f"Analytics took {query_time:.3f}s, should be under 2s"

        finally:
            # Cleanup
            from rivaflow.db.database import convert_query, get_connection

            with get_connection() as conn:
                cursor = conn.cursor()
                for session_id in session_ids:
                    cursor.execute(
                        convert_query("DELETE FROM sessions WHERE id = ?"),
                        (session_id,),
                    )

    def test_report_generation_performance(self):
        """Test report generation performance."""
        from rivaflow.core.services.report_service import ReportService

        user_id = 1
        service = ReportService()

        # Create 500 sessions over 6 months
        from rivaflow.db.repositories.session_repo import SessionRepository

        repo = SessionRepository()

        session_ids = []
        for i in range(500):
            session_id = repo.create(
                user_id=user_id,
                session_date=date.today() - timedelta(days=i % 180),
                class_type=["gi", "no-gi", "s&c"][i % 3],
                gym_name="Test Academy",
                duration_mins=60,
                intensity=4,
                rolls=5 if i % 3 < 2 else 0,
            )
            session_ids.append(session_id)

        try:
            # Test monthly report generation
            start_date, end_date = service.get_month_dates()

            start_time = time.time()
            report = service.generate_report(start_date, end_date)
            end_time = time.time()

            query_time = end_time - start_time
            print(f"\nMonthly report generation: {query_time:.3f}s")

            assert "summary" in report
            assert query_time < 1.0, f"Report generation took {query_time:.3f}s, should be under 1s"

        finally:
            # Cleanup
            from rivaflow.db.database import convert_query, get_connection

            with get_connection() as conn:
                cursor = conn.cursor()
                for session_id in session_ids:
                    cursor.execute(
                        convert_query("DELETE FROM sessions WHERE id = ?"),
                        (session_id,),
                    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
