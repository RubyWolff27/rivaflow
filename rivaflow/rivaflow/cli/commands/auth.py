"""CLI authentication commands."""
import json
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Prompt

from rivaflow.core.services.auth_service import AuthService

app = typer.Typer(help="Authentication commands")
console = Console()
auth_service = AuthService()

# Credentials file location
CREDENTIALS_FILE = Path.home() / ".rivaflow" / "credentials.json"


@app.command()
def login(
    email: str | None = typer.Option(None, "--email", "-e", help="Email address"),
    password: str | None = typer.Option(None, "--password", "-p", help="Password (not recommended, use prompt)"),
):
    """Login to RivaFlow CLI."""
    try:
        # Prompt for email if not provided
        if not email:
            email = Prompt.ask("[bold cyan]Email[/bold cyan]")

        # Prompt for password if not provided (secure, hidden input)
        if not password:
            password = Prompt.ask("[bold cyan]Password[/bold cyan]", password=True)

        # Authenticate with API
        console.print("[dim]Authenticating...[/dim]")
        result = auth_service.login(email=email, password=password)

        # Store credentials securely
        credentials_dir = CREDENTIALS_FILE.parent
        credentials_dir.mkdir(parents=True, exist_ok=True)

        credentials = {
            "user_id": result["user"]["id"],
            "email": result["user"]["email"],
            "first_name": result["user"].get("first_name"),
            "last_name": result["user"].get("last_name"),
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
        }

        # Write credentials file
        with open(CREDENTIALS_FILE, "w") as f:
            json.dump(credentials, f, indent=2)

        # Set secure file permissions (user read/write only)
        os.chmod(CREDENTIALS_FILE, 0o600)

        console.print(f"✅ [green]Logged in successfully as {result['user']['email']}[/green]")
        console.print(f"   Welcome back, {result['user'].get('first_name', 'User')}!")

    except ValueError as e:
        console.print(f"❌ [red]Authentication failed: {e}[/red]")
        console.print()
        console.print("[dim]Tips:[/dim]")
        console.print("  • Check that your email is correct")
        console.print("  • Passwords are case-sensitive")
        console.print("  • If you don't have an account: rivaflow auth register")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"❌ [red]Login error: {e}[/red]")
        console.print("[dim]If this persists, please report it at:[/dim]")
        console.print("  https://github.com/RubyWolff27/rivaflow/issues")
        raise typer.Exit(code=1)


@app.command()
def logout():
    """Logout from RivaFlow CLI."""
    try:
        # Check if logged in
        if not CREDENTIALS_FILE.exists():
            console.print("[yellow]Not currently logged in[/yellow]")
            return

        # Load credentials to get refresh token
        with open(CREDENTIALS_FILE) as f:
            credentials = json.load(f)

        # Invalidate refresh token on server
        try:
            auth_service.logout(credentials.get("refresh_token", ""))
        except Exception:
            # Even if server logout fails, remove local credentials
            pass

        # Remove credentials file
        CREDENTIALS_FILE.unlink()

        console.print("✅ [green]Logged out successfully[/green]")

    except Exception as e:
        console.print(f"❌ [red]Logout error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def register(
    email: str | None = typer.Option(None, "--email", "-e", help="Email address"),
    password: str | None = typer.Option(None, "--password", "-p", help="Password (not recommended, use prompt)"),
    first_name: str | None = typer.Option(None, "--first-name", "-f", help="First name"),
    last_name: str | None = typer.Option(None, "--last-name", "-l", help="Last name"),
):
    """Register a new RivaFlow account."""
    try:
        # Prompt for information if not provided
        if not email:
            email = Prompt.ask("[bold cyan]Email[/bold cyan]")

        if not first_name:
            first_name = Prompt.ask("[bold cyan]First name[/bold cyan]")

        if not last_name:
            last_name = Prompt.ask("[bold cyan]Last name[/bold cyan]")

        if not password:
            password = Prompt.ask("[bold cyan]Password (min 8 characters)[/bold cyan]", password=True)
            password_confirm = Prompt.ask("[bold cyan]Confirm password[/bold cyan]", password=True)

            if password != password_confirm:
                console.print("❌ [red]Passwords do not match[/red]")
                console.print("[dim]Hint: Make sure both password entries are identical[/dim]")
                raise typer.Exit(code=1)

            # Validate password length
            if len(password) < 8:
                console.print("❌ [red]Password must be at least 8 characters long[/red]")
                console.print("[dim]Tip: Use a mix of letters, numbers, and symbols for better security[/dim]")
                raise typer.Exit(code=1)

        # Register with API
        console.print("[dim]Creating account...[/dim]")
        result = auth_service.register(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # Store credentials securely
        credentials_dir = CREDENTIALS_FILE.parent
        credentials_dir.mkdir(parents=True, exist_ok=True)

        credentials = {
            "user_id": result["user"]["id"],
            "email": result["user"]["email"],
            "first_name": result["user"].get("first_name"),
            "last_name": result["user"].get("last_name"),
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
        }

        # Write credentials file
        with open(CREDENTIALS_FILE, "w") as f:
            json.dump(credentials, f, indent=2)

        # Set secure file permissions (user read/write only)
        os.chmod(CREDENTIALS_FILE, 0o600)

        console.print("✅ [green]Account created successfully![/green]")
        console.print(f"   Welcome to RivaFlow, {first_name}!")
        console.print(f"   Your account email: {email}")

    except ValueError as e:
        error_msg = str(e)
        if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
            console.print(f"❌ [red]An account with email '{email}' already exists[/red]")
            console.print()
            console.print("[dim]To login instead:[/dim]")
            console.print("  rivaflow auth login")
        else:
            console.print(f"❌ [red]Registration failed: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"❌ [red]Registration error: {e}[/red]")
        console.print("[dim]If this persists, please report it at:[/dim]")
        console.print("  https://github.com/RubyWolff27/rivaflow/issues")
        raise typer.Exit(code=1)


@app.command()
def whoami():
    """Display current logged-in user information."""
    try:
        if not CREDENTIALS_FILE.exists():
            console.print("[yellow]⚠ Not logged in[/yellow]")
            console.print()
            console.print("[dim]Login with:[/dim]")
            console.print("  rivaflow auth login")
            console.print()
            console.print("[dim]Or create a new account:[/dim]")
            console.print("  rivaflow auth register")
            return

        with open(CREDENTIALS_FILE) as f:
            credentials = json.load(f)

        console.print("[bold]Current User:[/bold]")
        console.print(f"  Name: {credentials.get('first_name')} {credentials.get('last_name')}")
        console.print(f"  Email: {credentials.get('email')}")
        console.print(f"  User ID: {credentials.get('user_id')}")

    except Exception as e:
        console.print(f"❌ [red]Error reading user info: {e}[/red]")
        console.print("[dim]Hint: Your credentials file may be corrupted. Try logging in again.[/dim]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
