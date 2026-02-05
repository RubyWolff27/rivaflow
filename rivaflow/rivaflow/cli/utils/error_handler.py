"""Centralized error handling for CLI commands.

Provides user-friendly error messages and recovery suggestions.
"""

import typer

from rivaflow.cli import prompts
from rivaflow.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DatabaseError,
    NotFoundError,
    RivaFlowException,
    ServiceError,
    ValidationError,
)


def handle_error(e: Exception, context: str = "") -> None:
    """Handle CLI errors with user-friendly messages.

    Args:
        e: Exception that occurred
        context: Additional context about what was being attempted
    """
    # Authentication errors
    if isinstance(e, AuthenticationError):
        prompts.print_error("Authentication failed")
        prompts.console.print("[dim]Please login first:[/dim]")
        prompts.console.print("  rivaflow auth login")
        prompts.console.print()
        prompts.console.print("[dim]Or create a new account:[/dim]")
        prompts.console.print("  rivaflow auth register")
        raise typer.Exit(1)

    # Authorization errors
    if isinstance(e, AuthorizationError):
        prompts.print_error(f"Permission denied: {e.message}")
        if context:
            prompts.console.print(f"[dim]While: {context}[/dim]")
        raise typer.Exit(1)

    # Validation errors
    if isinstance(e, ValidationError):
        prompts.print_error(f"Invalid input: {e.message}")
        if e.details:
            prompts.console.print("[dim]Details:[/dim]")
            for key, value in e.details.items():
                prompts.console.print(f"  • {key}: {value}")
        raise typer.Exit(1)

    # Not found errors
    if isinstance(e, NotFoundError):
        prompts.print_error(f"Not found: {e.message}")
        if context:
            prompts.console.print(f"[dim]Hint: {context}[/dim]")
        raise typer.Exit(1)

    # Conflict errors
    if isinstance(e, ConflictError):
        prompts.print_error(f"Conflict: {e.message}")
        prompts.console.print(
            "[dim]This data already exists or conflicts with existing records[/dim]"
        )
        raise typer.Exit(1)

    # Database errors
    if isinstance(e, DatabaseError):
        prompts.print_error("Database error occurred")
        prompts.console.print("[dim]Your data may be corrupted. Try:[/dim]")
        prompts.console.print("  1. Export your data: rivaflow export")
        prompts.console.print("  2. Check database integrity")
        prompts.console.print("  3. Contact support if the issue persists")
        prompts.console.print()
        prompts.console.print(f"[dim]Error details: {str(e)}[/dim]")
        raise typer.Exit(1)

    # Service errors
    if isinstance(e, ServiceError):
        prompts.print_error(f"Service error: {e.message}")
        prompts.console.print(
            "[dim]An internal error occurred. Please try again.[/dim]"
        )
        if context:
            prompts.console.print(f"[dim]Context: {context}[/dim]")
        raise typer.Exit(1)

    # Generic RivaFlow exceptions
    if isinstance(e, RivaFlowException):
        prompts.print_error(e.message)
        if e.details:
            prompts.console.print("[dim]Details:[/dim]")
            for key, value in e.details.items():
                prompts.console.print(f"  • {key}: {value}")
        raise typer.Exit(1)

    # Unexpected errors
    prompts.print_error("An unexpected error occurred")
    prompts.console.print(f"[dim]Error type: {type(e).__name__}[/dim]")
    prompts.console.print(f"[dim]Message: {str(e)}[/dim]")
    prompts.console.print()
    prompts.console.print("[dim]If this persists, please report it:[/dim]")
    prompts.console.print("  https://github.com/RubyWolff27/rivaflow/issues")
    raise typer.Exit(1)


def require_login() -> int:
    """Ensure user is logged in, raise friendly error if not.

    Returns:
        User ID if logged in

    Raises:
        typer.Exit: If user is not logged in
    """
    from rivaflow.cli.utils.user_context import get_current_user_id

    try:
        user_id = get_current_user_id()
        if user_id is None:
            raise AuthenticationError("Not logged in")
        return user_id
    except (FileNotFoundError, KeyError, ValueError):
        prompts.print_error("You must be logged in to use this command")
        prompts.console.print()
        prompts.console.print("[dim]Login with:[/dim]")
        prompts.console.print("  rivaflow auth login")
        prompts.console.print()
        prompts.console.print("[dim]Or create a new account:[/dim]")
        prompts.console.print("  rivaflow auth register")
        raise typer.Exit(1)
