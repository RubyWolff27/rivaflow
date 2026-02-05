#!/usr/bin/env python3
"""
Fix user tier - manually update user to lifetime premium beta status.
Run this script to update your user account to lifetime_premium tier.
"""
import os
import sys
from datetime import datetime

# Add parent directory to path so we can import rivaflow
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rivaflow.db.database import convert_query, get_connection


def fix_user_tier(user_email: str):
    """Update user to lifetime premium beta status."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # First, check current status
        cursor.execute(
            convert_query("SELECT id, email, subscription_tier, is_beta_user FROM users WHERE email = ?"),
            (user_email,)
        )
        user = cursor.fetchone()

        if not user:
            print(f"❌ User not found: {user_email}")
            return False

        user_dict = dict(user)
        print("\n📋 Current Status:")
        print(f"   User ID: {user_dict['id']}")
        print(f"   Email: {user_dict['email']}")
        print(f"   Tier: {user_dict.get('subscription_tier', 'NULL')}")
        print(f"   Beta User: {user_dict.get('is_beta_user', False)}")

        # Update to lifetime premium beta
        cursor.execute(
            convert_query("""
                UPDATE users
                SET subscription_tier = 'lifetime_premium',
                    is_beta_user = TRUE,
                    beta_joined_at = COALESCE(beta_joined_at, ?),
                    tier_expires_at = NULL
                WHERE email = ?
            """),
            (datetime.now(), user_email)
        )

        conn.commit()

        # Verify update
        cursor.execute(
            convert_query("SELECT id, email, subscription_tier, is_beta_user, beta_joined_at FROM users WHERE email = ?"),
            (user_email,)
        )
        updated_user = cursor.fetchone()
        updated_dict = dict(updated_user)

        print("\n✅ Updated Status:")
        print(f"   User ID: {updated_dict['id']}")
        print(f"   Email: {updated_dict['email']}")
        print(f"   Tier: {updated_dict.get('subscription_tier')}")
        print(f"   Beta User: {updated_dict.get('is_beta_user')}")
        print(f"   Beta Joined: {updated_dict.get('beta_joined_at')}")

        return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/fix_user_tier.py <user_email>")
        print("Example: python scripts/fix_user_tier.py user@example.com")
        sys.exit(1)

    user_email = sys.argv[1]
    print(f"🔧 Fixing user tier for: {user_email}")

    success = fix_user_tier(user_email)

    if success:
        print(f"\n✨ Success! User {user_email} has been upgraded to lifetime_premium beta status.")
        print("   Please log out and log back in to see the changes.")
    else:
        print(f"\n❌ Failed to update user {user_email}")
        sys.exit(1)
