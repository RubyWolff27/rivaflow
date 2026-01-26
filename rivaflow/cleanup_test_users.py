"""Cleanup test users and their data."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rivaflow.db.repositories.user_repo import UserRepository
from rivaflow.db.database import get_connection

print("=" * 60)
print("Cleaning Up Test Users")
print("=" * 60)

# Test user emails
test_emails = [
    "alice.bjj@test.com",
    "bob.grappler@test.com",
    "charlie.rolls@test.com",
]

test_user_ids = []

# Find test users
print("\n1. Finding test users...")
for email in test_emails:
    user = UserRepository.get_by_email(email)
    if user:
        test_user_ids.append(user['id'])
        print(f"   ✓ Found {user['first_name']} {user['last_name']} (ID: {user['id']})")
    else:
        print(f"   ⚠️  User {email} not found")

if not test_user_ids:
    print("\n✓ No test users found. Already clean!")
    sys.exit(0)

# Delete all data for test users
print("\n2. Deleting test user data...")
with get_connection() as conn:
    cursor = conn.cursor()

    for user_id in test_user_ids:
        # Delete sessions
        cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        session_count = cursor.rowcount

        # Delete readiness
        cursor.execute("DELETE FROM readiness WHERE user_id = ?", (user_id,))
        readiness_count = cursor.rowcount

        # Delete checkins
        cursor.execute("DELETE FROM daily_checkins WHERE user_id = ?", (user_id,))
        checkin_count = cursor.rowcount

        # Delete relationships (both follower and following)
        cursor.execute("DELETE FROM user_relationships WHERE follower_user_id = ? OR following_user_id = ?", (user_id, user_id))
        relationship_count = cursor.rowcount

        # Delete likes
        cursor.execute("DELETE FROM activity_likes WHERE user_id = ?", (user_id,))
        like_count = cursor.rowcount

        # Delete comments
        cursor.execute("DELETE FROM activity_comments WHERE user_id = ?", (user_id,))
        comment_count = cursor.rowcount

        # Delete profile
        cursor.execute("DELETE FROM profile WHERE user_id = ?", (user_id,))

        # Delete user
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

        print(f"   ✓ User ID {user_id}: {session_count} sessions, {readiness_count} readiness, {checkin_count} checkins")
        print(f"     {relationship_count} relationships, {like_count} likes, {comment_count} comments")

print("\n" + "=" * 60)
print("Cleanup Complete!")
print("=" * 60)
print(f"\n✓ Removed {len(test_user_ids)} test users and all their data")
print("=" * 60)
