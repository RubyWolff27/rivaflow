"""Create test users with dummy data for social features testing."""
import sys
from datetime import date, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rivaflow.core.services.auth_service import AuthService
from rivaflow.db.repositories import ReadinessRepository, SessionRepository
from rivaflow.db.repositories.activity_comment_repo import ActivityCommentRepository
from rivaflow.db.repositories.activity_like_repo import ActivityLikeRepository
from rivaflow.db.repositories.checkin_repo import CheckinRepository
from rivaflow.db.repositories.relationship_repo import UserRelationshipRepository
from rivaflow.db.repositories.user_repo import UserRepository

print("=" * 60)
print("Creating Test Users for Social Features Testing")
print("=" * 60)

# Test users data
test_users = [
    {
        "email": "alice.bjj@test.com",
        "password": "testpass123",
        "first_name": "Alice",
        "last_name": "Anderson",
    },
    {
        "email": "bob.grappler@test.com",
        "password": "testpass123",
        "first_name": "Bob",
        "last_name": "Brown",
    },
    {
        "email": "charlie.rolls@test.com",
        "password": "testpass123",
        "first_name": "Charlie",
        "last_name": "Chen",
    },
]

user_ids = []

# Create users
print("\n1. Creating test users...")
auth_service = AuthService()
user_repo = UserRepository()
for user_data in test_users:
    try:
        # Check if user already exists
        existing = user_repo.get_by_email(user_data["email"])
        if existing:
            print(f"   ⚠️  User {user_data['email']} already exists (ID: {existing['id']})")
            user_ids.append(existing['id'])
        else:
            result = auth_service.register(
                email=user_data["email"],
                password=user_data["password"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
            )
            user_ids.append(result["user"]["id"])
            print(f"   ✓ Created {user_data['first_name']} {user_data['last_name']} (ID: {result['user']['id']})")
    except Exception as e:
        print(f"   ✗ Error creating {user_data['email']}: {e}")

if len(user_ids) != 3:
    print("\n✗ Failed to create all users. Exiting.")
    sys.exit(1)

alice_id, bob_id, charlie_id = user_ids

# Create sessions for each user
print("\n2. Creating training sessions...")
session_repo = SessionRepository()

# Alice's sessions (mixture of visibility levels)
alice_sessions = []
for i in range(5):
    days_ago = i * 2
    session_date = date.today() - timedelta(days=days_ago)
    visibility = ['private', 'attendance', 'summary', 'full', 'summary'][i]

    session_id = session_repo.create(
        user_id=alice_id,
        session_date=session_date,
        class_type=['gi', 'no-gi', 'open-mat', 'gi', 'no-gi'][i],
        gym_name="Alliance BJJ",
        location="San Diego, CA",
        duration_mins=90,
        intensity=[4, 5, 3, 4, 5][i],
        rolls=[5, 6, 4, 5, 7][i],
        submissions_for=[2, 3, 1, 2, 3][i],
        submissions_against=[1, 2, 1, 1, 2][i],
        partners=["Bob", "Charlie", "Training Partner"],
        techniques=["Triangle choke", "Armbar", "Kimura"],
        notes=f"Great session! Worked on guard passing and submissions. Day {i+1}.",
        visibility_level=visibility,
    )
    alice_sessions.append(session_id)
    print(f"   ✓ Alice: {visibility.upper()} session on {session_date}")

# Bob's sessions (mostly shareable)
bob_sessions = []
for i in range(4):
    days_ago = i * 3 + 1
    session_date = date.today() - timedelta(days=days_ago)
    visibility = ['summary', 'full', 'attendance', 'full'][i]

    session_id = session_repo.create(
        user_id=bob_id,
        session_date=session_date,
        class_type=['gi', 'no-gi', 'gi', 'open-mat'][i],
        gym_name="Gracie Barra",
        location="Austin, TX",
        duration_mins=75,
        intensity=[3, 4, 4, 5][i],
        rolls=[4, 5, 3, 6][i],
        submissions_for=[1, 2, 1, 3][i],
        submissions_against=[2, 1, 2, 1][i],
        partners=["Alice", "Training buddy"],
        techniques=["Rear naked choke", "Guillotine", "Sweep"],
        notes=f"Focused on technique and positioning. Session {i+1}.",
        visibility_level=visibility,
    )
    bob_sessions.append(session_id)
    print(f"   ✓ Bob: {visibility.upper()} session on {session_date}")

# Charlie's sessions (all shareable)
charlie_sessions = []
for i in range(3):
    days_ago = i * 4 + 2
    session_date = date.today() - timedelta(days=days_ago)
    visibility = ['full', 'summary', 'full'][i]

    session_id = session_repo.create(
        user_id=charlie_id,
        session_date=session_date,
        class_type=['gi', 'no-gi', 'gi'][i],
        gym_name="10th Planet",
        location="Los Angeles, CA",
        duration_mins=80,
        intensity=[5, 4, 4][i],
        rolls=[8, 6, 5][i],
        submissions_for=[4, 2, 3][i],
        submissions_against=[1, 2, 1][i],
        partners=["Multiple partners", "Bob", "Alice"],
        techniques=["Rubber guard", "Twister", "Electric chair"],
        notes=f"Intense rolling session with lots of sparring. Day {i+1}.",
        visibility_level=visibility,
    )
    charlie_sessions.append(session_id)
    print(f"   ✓ Charlie: {visibility.upper()} session on {session_date}")

# Create readiness check-ins
print("\n3. Creating readiness check-ins...")
readiness_repo = ReadinessRepository()

# Alice's readiness (using days 0, 3, 6)
alice_readiness_dates = [0, 3, 6]
for i, days_ago in enumerate(alice_readiness_dates):
    check_date = date.today() - timedelta(days=days_ago)
    try:
        readiness_repo.upsert(
            user_id=alice_id,
            check_date=check_date,
            sleep=[4, 5, 3][i],
            stress=[2, 1, 3][i],
            soreness=[3, 2, 4][i],
            energy=[4, 5, 3][i],
            weight_kg=65.5,
        )
    except Exception as e:
        print(f"   ⚠️  Alice readiness on {check_date}: {e}")
print("   ✓ Alice: readiness check-ins")

# Bob's readiness (using days 1, 7 to avoid conflicts)
bob_readiness_dates = [1, 7]
for i, days_ago in enumerate(bob_readiness_dates):
    check_date = date.today() - timedelta(days=days_ago)
    try:
        readiness_repo.upsert(
            user_id=bob_id,
            check_date=check_date,
            sleep=[5, 4][i],
            stress=[1, 2][i],
            soreness=[2, 3][i],
            energy=[5, 4][i],
            weight_kg=82.0,
        )
    except Exception as e:
        print(f"   ⚠️  Bob readiness on {check_date}: {e}")
print("   ✓ Bob: readiness check-ins")

# Create some rest days
print("\n4. Creating rest days...")
checkin_repo = CheckinRepository()

# Charlie takes a rest day
rest_date = date.today() - timedelta(days=5)
try:
    checkin_repo.upsert_checkin(
        user_id=charlie_id,
        check_date=rest_date,
        checkin_type="rest",
        rest_type="recovery",
        rest_note="Active recovery day - light stretching and mobility work",
    )
    print(f"   ✓ Charlie: Rest day on {rest_date}")
except Exception as e:
    print(f"   ⚠️  Charlie rest day: {e}")

# Set up follow relationships
print("\n5. Setting up follow relationships...")
relationship_repo = UserRelationshipRepository()

# Alice follows Bob and Charlie
try:
    relationship_repo.follow(alice_id, bob_id)
    print("   ✓ Alice follows Bob")
except Exception as e:
    if "unique" in str(e).lower() or "already" in str(e).lower():
        print("   ⚠️  Alice already follows Bob")
    else:
        print(f"   ✗ Error: {e}")

try:
    relationship_repo.follow(alice_id, charlie_id)
    print("   ✓ Alice follows Charlie")
except Exception as e:
    if "unique" in str(e).lower() or "already" in str(e).lower():
        print("   ⚠️  Alice already follows Charlie")
    else:
        print(f"   ✗ Error: {e}")

# Bob follows Alice and Charlie
try:
    relationship_repo.follow(bob_id, alice_id)
    print("   ✓ Bob follows Alice")
except Exception as e:
    if "unique" in str(e).lower() or "already" in str(e).lower():
        print("   ⚠️  Bob already follows Alice")
    else:
        print(f"   ✗ Error: {e}")

try:
    relationship_repo.follow(bob_id, charlie_id)
    print("   ✓ Bob follows Charlie")
except Exception as e:
    if "unique" in str(e).lower() or "already" in str(e).lower():
        print("   ⚠️  Bob already follows Charlie")
    else:
        print(f"   ✗ Error: {e}")

# Charlie follows Alice
try:
    relationship_repo.follow(charlie_id, alice_id)
    print("   ✓ Charlie follows Alice")
except Exception as e:
    if "unique" in str(e).lower() or "already" in str(e).lower():
        print("   ⚠️  Charlie already follows Alice")
    else:
        print(f"   ✗ Error: {e}")

# Add some likes
print("\n6. Adding likes...")
like_repo = ActivityLikeRepository()

# Bob likes Alice's sessions
for session_id in alice_sessions[1:3]:  # Like some of Alice's shareable sessions
    try:
        like_repo.create(bob_id, 'session', session_id)
        print(f"   ✓ Bob liked Alice's session {session_id}")
    except Exception as e:
        if "unique" in str(e).lower() or "already" in str(e).lower():
            print(f"   ⚠️  Bob already liked session {session_id}")
        else:
            print(f"   ✗ Error: {e}")

# Alice likes Bob's sessions
for session_id in bob_sessions[0:2]:
    try:
        like_repo.create(alice_id, 'session', session_id)
        print(f"   ✓ Alice liked Bob's session {session_id}")
    except Exception as e:
        if "unique" in str(e).lower() or "already" in str(e).lower():
            print(f"   ⚠️  Alice already liked session {session_id}")
        else:
            print(f"   ✗ Error: {e}")

# Charlie likes everyone's sessions
try:
    like_repo.create(charlie_id, 'session', alice_sessions[2])
    print(f"   ✓ Charlie liked Alice's session {alice_sessions[2]}")
except Exception as e:
    if "unique" in str(e).lower() or "already" in str(e).lower():
        print("   ⚠️  Charlie already liked the session")
    else:
        print(f"   ✗ Error: {e}")

try:
    like_repo.create(charlie_id, 'session', bob_sessions[1])
    print(f"   ✓ Charlie liked Bob's session {bob_sessions[1]}")
except Exception as e:
    if "unique" in str(e).lower() or "already" in str(e).lower():
        print("   ⚠️  Charlie already liked the session")
    else:
        print(f"   ✗ Error: {e}")

# Add some comments
print("\n7. Adding comments...")
comment_repo = ActivityCommentRepository()

# Bob comments on Alice's session
try:
    comment_repo.create(
        bob_id,
        'session',
        alice_sessions[1],
        "Great work! Your guard passing is getting really sharp 🔥"
    )
    print("   ✓ Bob commented on Alice's session")
except Exception as e:
    print(f"   ⚠️  Error adding Bob's comment: {e}")

# Alice comments on Bob's session
try:
    comment_repo.create(
        alice_id,
        'session',
        bob_sessions[0],
        "Nice session! Those sweeps were looking clean 👍"
    )
    print("   ✓ Alice commented on Bob's session")
except Exception as e:
    print(f"   ⚠️  Error adding Alice's comment: {e}")

# Charlie comments on Alice's session
try:
    comment_repo.create(
        charlie_id,
        'session',
        alice_sessions[3],
        "Keep it up! Love the intensity 💪"
    )
    print("   ✓ Charlie commented on Alice's session")
except Exception as e:
    print(f"   ⚠️  Error adding Charlie's comment: {e}")

# Summary
print("\n" + "=" * 60)
print("Test Data Creation Complete!")
print("=" * 60)
print("\n📊 Summary:")
print("   Users created: 3")
print(f"   - Alice Anderson (ID: {alice_id}) - alice.bjj@test.com")
print(f"   - Bob Brown (ID: {bob_id}) - bob.grappler@test.com")
print(f"   - Charlie Chen (ID: {charlie_id}) - charlie.rolls@test.com")
print(f"\n   Total sessions: {len(alice_sessions) + len(bob_sessions) + len(charlie_sessions)}")
print(f"   - Alice: {len(alice_sessions)} sessions (mixed privacy)")
print(f"   - Bob: {len(bob_sessions)} sessions (mostly shareable)")
print(f"   - Charlie: {len(charlie_sessions)} sessions (all shareable)")
print("\n   Follow relationships: 5")
print("   Social interactions: ~10 likes and comments")
print("\n🔑 Login credentials (all users):")
print("   Password: testpass123")
print("\n🧪 Testing scenarios:")
print("   1. Login as Alice → See Bob & Charlie's activities in Contacts feed")
print("   2. Login as Bob → See Alice & Charlie's activities")
print("   3. Login as Charlie → See Alice's activities")
print("   4. Test privacy: Alice's private session should NOT appear in feeds")
print("   5. Test likes & comments on shareable activities")
print("\n🗑️  To remove test data later, run:")
print("   python cleanup_test_users.py")
print("=" * 60)
