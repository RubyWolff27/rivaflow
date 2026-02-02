# Python Docstring Style Guide

## Overview

RivaFlow follows Google-style docstrings with specific conventions for consistency across the codebase.

## General Rules

1. **All public functions, classes, and methods MUST have docstrings**
2. **Private functions (`_function`) MAY have docstrings** if logic is complex
3. **Use triple double-quotes** (`"""`) for all docstrings
4. **One-line summary** followed by blank line if more detail needed
5. **Use present tense** ("Return value" not "Returns value")
6. **Be concise** but complete

## Module Docstrings

Place at the top of the file:

```python
"""Service layer for training session operations."""
from datetime import date
```

**Bad:**
```python
"""
This module contains the session service
which handles session operations.
"""
```

**Good:**
```python
"""Service layer for training session operations."""
```

## Class Docstrings

```python
class SessionService:
    """Business logic for training sessions."""

    def __init__(self):
        self.session_repo = SessionRepository()
```

**For complex classes, add detail:**

```python
class AnalyticsService:
    """
    Business logic for analytics and dashboard data.

    Provides methods for generating:
    - Performance analytics
    - Partner statistics
    - Technique mastery tracking
    - Streak analysis
    """
```

## Function/Method Docstrings

### Simple Functions

One-line docstring is sufficient:

```python
def get_session(self, user_id: int, session_id: int) -> Optional[dict]:
    """Get a session by ID."""
    return self.session_repo.get_by_id(user_id, session_id)
```

### Complex Functions

Use Google-style format:

```python
def create_session(
    self,
    user_id: int,
    session_date: date,
    class_type: str,
    gym_name: str,
    **kwargs
) -> int:
    """
    Create a new training session and update technique tracking.

    Supports both simple mode (aggregate counts) and detailed mode
    (individual rolls and techniques).

    Args:
        user_id: User ID
        session_date: Date of the training session
        class_type: Type of class (gi, no-gi, etc.)
        gym_name: Name of gym or academy
        **kwargs: Additional session fields (duration, intensity, etc.)

    Returns:
        Session ID of the created session

    Raises:
        ValueError: If session_date is in the future
        ValidationError: If required fields are missing
    """
```

## Section Headers

### Args

- One line per argument
- Format: `name: description`
- Start description with capital letter
- No period if single sentence
- Use period if multiple sentences

```python
Args:
    user_id: User ID
    start_date: Start of date range. Defaults to 90 days ago.
    end_date: End of date range. Defaults to today.
```

### Returns

- Describe what is returned
- Include type information if not obvious from type hint
- Describe structure for complex returns

```python
Returns:
    Session ID of the created session
```

```python
Returns:
    Dict with performance metrics:
        - submission_success_over_time: Monthly breakdown
        - training_volume_calendar: Daily session data
        - top_submissions: Top 5 subs given and received
```

### Raises

- List exceptions that callers should handle
- Don't list exceptions from implementation details
- Format: `ExceptionType: When it's raised`

```python
Raises:
    ValueError: If date is in the future
    AuthenticationError: If user is not authenticated
```

### Examples (Optional)

For complex usage:

```python
Examples:
    Basic usage:
        >>> service = SessionService()
        >>> session_id = service.create_session(
        ...     user_id=1,
        ...     session_date=date.today(),
        ...     class_type="gi",
        ...     gym_name="Gracie Barra"
        ... )

    With optional fields:
        >>> session_id = service.create_session(
        ...     user_id=1,
        ...     session_date=date.today(),
        ...     class_type="gi",
        ...     gym_name="Gracie Barra",
        ...     duration_mins=90,
        ...     intensity=5
        ... )
```

## Type Hints

Type hints are preferred over documenting types in docstrings:

**Bad:**
```python
def get_session(user_id, session_id):
    """
    Get a session by ID.

    Args:
        user_id (int): User ID
        session_id (int): Session ID

    Returns:
        dict: Session data or None if not found
    """
```

**Good:**
```python
def get_session(self, user_id: int, session_id: int) -> Optional[dict]:
    """Get a session by ID."""
```

## Common Patterns

### Repository Methods

```python
def get_by_id(self, user_id: int, session_id: int) -> Optional[dict]:
    """Get a session by ID with detailed techniques."""

def create(self, user_id: int, session_date: date, **kwargs) -> int:
    """Create a new session and return its ID."""

def update(self, user_id: int, session_id: int, **kwargs) -> Optional[dict]:
    """Update a session by ID. Return updated session or None if not found."""

def delete(self, user_id: int, session_id: int) -> bool:
    """Delete a session by ID. Return True if deleted, False if not found."""
```

### Service Methods

```python
def get_performance_overview(
    self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Get performance overview metrics.

    Returns:
        Dict with submission success, training volume, and performance data
    """
```

### Helper Functions

Private helpers can have minimal docstrings:

```python
def _calculate_period_summary(self, sessions: List[Dict]) -> Dict[str, Any]:
    """Calculate summary metrics for a period with safe null handling."""
```

## Property Docstrings

```python
@property
def composite_score(self) -> int:
    """Calculate composite readiness score (4-20 range, higher is better)."""
    return self.sleep + (6 - self.stress) + (6 - self.soreness) + self.energy
```

## CLI Command Docstrings

Use Typer-friendly format with `\b` blocks:

```python
@app.command()
def log(quick: bool = typer.Option(False, "--quick", "-q")):
    """
    Log a training session with detailed tracking.

    \b
    Examples:
      $ rivaflow log           # Full mode
      $ rivaflow log --quick   # Quick mode
    """
```

## Deprecated Functions

```python
def old_function(self):
    """
    Calculate metrics (deprecated).

    .. deprecated:: 0.2.0
        Use :func:`new_function` instead.
    """
```

## TODOs in Docstrings

```python
def future_feature(self):
    """
    Placeholder for future feature.

    TODO: Implement actual logic after MVP release.
    """
```

## Anti-Patterns

### Don't:

❌ Repeat the function name
```python
def create_session(self):
    """Create session."""  # Too obvious
```

❌ Use "this function" or "this method"
```python
def get_session(self):
    """This function gets a session."""  # Verbose
```

❌ Document obvious parameters
```python
def add(a: int, b: int) -> int:
    """
    Add two numbers.

    Args:
        a: The first number  # Obvious from name
        b: The second number  # Obvious from name
    """
```

❌ Incomplete sentences
```python
def process(self):
    """Processes data and"""  # Incomplete
```

### Do:

✅ Be concise and clear
```python
def create_session(self):
    """Create a new training session and update technique tracking."""
```

✅ Focus on what, not how
```python
def get_session(self):
    """Get a session by ID."""  # Not: "Query database for session"
```

✅ Use active voice
```python
def calculate_streak(self):
    """Calculate current and longest training streaks."""
```

## Validation

Check docstring quality with:

```bash
# Check docstring coverage
pydocstyle rivaflow/

# Generate documentation
python -m pydoc rivaflow.core.services.session_service
```

## Examples by File Type

### Services (`core/services/`)
- Always include full docstrings for public methods
- Describe what the method accomplishes, not how
- Include Args/Returns for complex methods

### Repositories (`db/repositories/`)
- Focus on data operations
- Mention what is returned (dict, list, bool, etc.)
- Note if None is returned for not found

### CLI Commands (`cli/commands/`)
- Use Typer-friendly formatting
- Include examples in docstring
- Focus on user perspective

### Utilities (`cli/utils/`, `core/`)
- Brief but complete
- Mention edge cases if relevant

---

**Last Updated:** 2026-02-02
**Related:** Task #29 from BETA_READINESS_REPORT.md
