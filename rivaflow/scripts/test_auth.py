#!/usr/bin/env python3
"""Diagnostic script to test authentication and bcrypt compatibility."""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set environment variables for testing
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-diagnostics")
os.environ.setdefault(
    "DATABASE_URL", "postgresql://user:pass@localhost/rivaflow"
)  # Update as needed

from rivaflow.core.auth import hash_password, verify_password
from rivaflow.db.repositories.user_repo import UserRepository


def test_bcrypt_compatibility():
    """Test bcrypt 4.x compatibility with password hashing."""
    print("=" * 60)
    print("BCRYPT COMPATIBILITY TEST")
    print("=" * 60)

    # Test password hashing and verification
    test_password = "TestPassword123!"

    print("\n1. Testing password hashing...")
    hashed = hash_password(test_password)
    print(f"   ✓ Hash created: {hashed[:20]}...")

    print("\n2. Testing password verification (same password)...")
    is_valid = verify_password(test_password, hashed)
    print(f"   {'✓' if is_valid else '✗'} Verification: {is_valid}")

    print("\n3. Testing password verification (wrong password)...")
    is_valid = verify_password("WrongPassword", hashed)
    print(f"   {'✓' if not is_valid else '✗'} Verification: {is_valid} (should be False)")

    return True


def test_existing_users():
    """Check existing users in database."""
    print("\n" + "=" * 60)
    print("EXISTING USERS CHECK")
    print("=" * 60)

    try:
        from rivaflow.db.database import get_connection

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, email, first_name, last_name, is_active, created_at
                FROM users
                ORDER BY created_at DESC
                LIMIT 5
            """
            )
            users = cursor.fetchall()

            if not users:
                print("\n⚠ No users found in database")
                return False

            print(f"\nFound {len(users)} recent user(s):")
            for user in users:
                print(f"   • ID: {user[0]}, Email: {user[1]}, Active: {user[4]}")

            return True

    except Exception as e:
        print(f"\n✗ Database error: {e}")
        return False


def test_user_login(email: str, password: str):
    """Test login for a specific user."""
    print("\n" + "=" * 60)
    print(f"LOGIN TEST: {email}")
    print("=" * 60)

    try:
        user_repo = UserRepository()

        # Get user
        print("\n1. Fetching user by email...")
        user = user_repo.get_by_email(email)

        if not user:
            print(f"   ✗ User not found: {email}")
            return False

        print(f"   ✓ User found: ID={user['id']}, Active={user.get('is_active')}")

        # Check if active
        if not user.get("is_active"):
            print("   ✗ User account is inactive")
            return False

        # Verify password
        print("\n2. Verifying password...")
        hashed_password = user.get("hashed_password")

        if not hashed_password:
            print("   ✗ No password hash found for user")
            return False

        print(f"   Hash format: {hashed_password[:20]}...")
        is_valid = verify_password(password, hashed_password)

        if is_valid:
            print("   ✓ Password verified successfully")
            return True
        else:
            print("   ✗ Password verification failed")
            return False

    except Exception as e:
        print(f"\n✗ Error during login test: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all diagnostic tests."""
    print("\n🔍 RivaFlow Authentication Diagnostics")
    print("=" * 60)

    # Test 1: Bcrypt compatibility
    test_bcrypt_compatibility()

    # Test 2: Check existing users
    test_existing_users()

    # Test 3: Optional - test specific user login
    if len(sys.argv) >= 3:
        email = sys.argv[1]
        password = sys.argv[2]
        test_user_login(email, password)
    else:
        print("\n" + "=" * 60)
        print("USAGE FOR SPECIFIC USER TEST")
        print("=" * 60)
        print("\nTo test a specific user login:")
        print(f"  python {sys.argv[0]} <email> <password>")

    print("\n" + "=" * 60)
    print("Diagnostics complete")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
