#!/usr/bin/env python3
"""Manage admin users for RivaFlow."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def list_admins():
    """List all admin users."""
    from rivaflow.db.database import convert_query, get_connection

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query(
                """
            SELECT id, email, first_name, last_name, is_admin, created_at
            FROM users
            WHERE is_admin = 1
            ORDER BY id
        """
            )
        )
        admins = cursor.fetchall()

    print("\n" + "=" * 80)
    print("ADMIN USERS")
    print("=" * 80)

    if not admins:
        print("No admin users found.")
    else:
        for admin in admins:
            admin_dict = dict(admin)
            print(f"\nID: {admin_dict['id']}")
            print(f"Email: {admin_dict['email']}")
            print(f"Name: {admin_dict['first_name']} {admin_dict['last_name']}")
            print(f"Created: {admin_dict['created_at']}")

    print()


def list_users():
    """List all users."""
    from rivaflow.db.database import convert_query, get_connection

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query(
                """
            SELECT id, email, first_name, last_name, is_admin, is_active
            FROM users
            ORDER BY id
        """
            )
        )
        users = cursor.fetchall()

    print("\n" + "=" * 80)
    print("ALL USERS")
    print("=" * 80)

    for user in users:
        user_dict = dict(user)
        admin_badge = "👑 ADMIN" if user_dict["is_admin"] else ""
        active_badge = "✓ Active" if user_dict["is_active"] else "✗ Inactive"

        print(
            f"\n[{user_dict['id']}] {user_dict['email']} - {user_dict['first_name']} {user_dict['last_name']}"
        )
        print(f"    {active_badge} {admin_badge}")

    print()


def grant_admin(user_id: int):
    """Grant admin privileges to a user."""
    from rivaflow.db.database import convert_query, get_connection

    with get_connection() as conn:
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute(
            convert_query(
                "SELECT id, email, first_name, last_name FROM users WHERE id = ?"
            ),
            (user_id,),
        )
        user = cursor.fetchone()

        if not user:
            print(f"❌ User with ID {user_id} not found.")
            return False

        user_dict = dict(user)

        # Grant admin
        cursor.execute(
            convert_query("UPDATE users SET is_admin = 1 WHERE id = ?"), (user_id,)
        )
        conn.commit()

        print("✅ Admin privileges granted to:")
        print(f"   User ID: {user_dict['id']}")
        print(f"   Email: {user_dict['email']}")
        print(f"   Name: {user_dict['first_name']} {user_dict['last_name']}")

    return True


def revoke_admin(user_id: int):
    """Revoke admin privileges from a user."""
    from rivaflow.db.database import convert_query, get_connection

    with get_connection() as conn:
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute(
            convert_query(
                "SELECT id, email, first_name, last_name FROM users WHERE id = ?"
            ),
            (user_id,),
        )
        user = cursor.fetchone()

        if not user:
            print(f"❌ User with ID {user_id} not found.")
            return False

        user_dict = dict(user)

        # Revoke admin
        cursor.execute(
            convert_query("UPDATE users SET is_admin = 0 WHERE id = ?"), (user_id,)
        )
        conn.commit()

        print("✅ Admin privileges revoked from:")
        print(f"   User ID: {user_dict['id']}")
        print(f"   Email: {user_dict['email']}")
        print(f"   Name: {user_dict['first_name']} {user_dict['last_name']}")

    return True


def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print("\nRivaFlow Admin Management")
        print("=" * 80)
        print("\nUsage:")
        print(
            "  python rivaflow/scripts/manage_admins.py list         # List all admin users"
        )
        print(
            "  python rivaflow/scripts/manage_admins.py users        # List all users"
        )
        print(
            "  python rivaflow/scripts/manage_admins.py grant <id>   # Grant admin to user"
        )
        print(
            "  python rivaflow/scripts/manage_admins.py revoke <id>  # Revoke admin from user"
        )
        print()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "list":
        list_admins()
    elif command == "users":
        list_users()
    elif command == "grant":
        if len(sys.argv) < 3:
            print("❌ Error: User ID required")
            print("Usage: python rivaflow/scripts/manage_admins.py grant <user_id>")
            sys.exit(1)
        try:
            user_id = int(sys.argv[2])
            grant_admin(user_id)
        except ValueError:
            print("❌ Error: User ID must be a number")
            sys.exit(1)
    elif command == "revoke":
        if len(sys.argv) < 3:
            print("❌ Error: User ID required")
            print("Usage: python rivaflow/scripts/manage_admins.py revoke <user_id>")
            sys.exit(1)
        try:
            user_id = int(sys.argv[2])
            revoke_admin(user_id)
        except ValueError:
            print("❌ Error: User ID must be a number")
            sys.exit(1)
    else:
        print(f"❌ Unknown command: {command}")
        print("Valid commands: list, users, grant, revoke")
        sys.exit(1)


if __name__ == "__main__":
    main()
