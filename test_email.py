#!/usr/bin/env python3
"""Test email service configuration."""
import os
import sys

# Add rivaflow to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rivaflow.core.services.email_service import EmailService

def test_email_config():
    """Test email service configuration and send test email."""

    print("=" * 60)
    print("Email Service Configuration Test")
    print("=" * 60)

    # Show current environment variables
    print("\nEnvironment Variables:")
    print(f"SMTP_USER: {'SET' if os.getenv('SMTP_USER') else 'NOT SET'}")
    print(f"SMTP_PASSWORD: {'SET (length: {})'.format(len(os.getenv('SMTP_PASSWORD', ''))) if os.getenv('SMTP_PASSWORD') else 'NOT SET'}")
    print(f"SMTP_HOST: {os.getenv('SMTP_HOST', 'smtp.gmail.com (default)')}")
    print(f"SMTP_PORT: {os.getenv('SMTP_PORT', '587 (default)')}")
    print(f"FROM_EMAIL: {os.getenv('FROM_EMAIL', 'SMTP_USER (default)')}")
    print(f"FROM_NAME: {os.getenv('FROM_NAME', 'RivaFlow (default)')}")

    # Initialize email service
    print("\nInitializing Email Service...")
    email_service = EmailService()

    print(f"Email Service Enabled: {email_service.enabled}")

    if not email_service.enabled:
        print("\n❌ Email service is NOT enabled!")
        print("\nTo fix this, set environment variables:")
        print("  export SMTP_USER='your-email@gmail.com'")
        print("  export SMTP_PASSWORD='your-app-password'")
        print("\nFor Gmail, generate an App Password at:")
        print("  https://myaccount.google.com/apppasswords")
        return False

    print("\n✅ Email service is enabled!")

    # Ask if user wants to send test email
    test_email = input("\nEnter email address to send test to (or press Enter to skip): ").strip()

    if test_email:
        print(f"\nSending test email to {test_email}...")
        success = email_service.send_password_reset_email(
            to_email=test_email,
            reset_token="test-token-12345",
            user_name="Test User"
        )

        if success:
            print("✅ Test email sent successfully!")
            print("Check your inbox (and spam folder)")
        else:
            print("❌ Failed to send test email")
            print("Check the logs above for error details")

        return success

    return True

if __name__ == "__main__":
    test_email_config()
