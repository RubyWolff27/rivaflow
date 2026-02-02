# Progress Indicators Guide

## Overview

RivaFlow CLI uses Rich library's `status()` context manager to display progress spinners for long-running operations (>1 second). This provides visual feedback that the application is working and prevents users from thinking the CLI has frozen.

## When to Use Progress Indicators

Add spinners for operations that:
- Take longer than 1 second
- Involve multiple database queries
- Process large amounts of data
- Calculate complex analytics or aggregations
- Export or import data

## Implementation Pattern

### Basic Usage

```python
from rich.console import Console

console = Console()

# Wrap long-running operation with spinner
with console.status("[cyan]Loading data...", spinner="dots"):
    # Your long-running operation here
    result = expensive_operation()
```

### Standard Spinner Messages

Use consistent, action-oriented messages:

| Operation | Message |
|-----------|---------|
| Report generation | `"Generating weekly report..."` |
| Analytics loading | `"Calculating analytics..."` |
| Data export | `"Exporting your data..."` |
| Dashboard loading | `"Loading dashboard..."` |
| Milestone calculation | `"Calculating streaks and milestones..."` |
| Stats aggregation | `"Loading lifetime stats..."` |

### Message Style Guidelines

✅ **DO:**
- Use present continuous tense ("Loading...", "Generating...")
- Be specific about what's happening
- Use cyan color for consistency: `"[cyan]Message..."`
- Use "dots" spinner for consistency

❌ **DON'T:**
- Use vague messages ("Please wait...")
- Use passive voice ("Data is being loaded...")
- Use different colors or spinners (stick to cyan and dots)
- Add exclamation points or excessive punctuation

## Examples by Command Type

### Report Commands

```python
# rivaflow/cli/commands/report.py

@app.command()
def week(csv: bool = False, output: Optional[str] = None):
    """Show current week training report."""
    service = ReportService()
    start_date, end_date = service.get_week_dates()

    with console.status("[cyan]Generating weekly report...", spinner="dots"):
        report = service.generate_report(start_date, end_date)

    if csv or output:
        _export_csv(service, report, output or "week_report.csv")
    else:
        _display_report(report, "WEEKLY REPORT")
```

### Dashboard Commands

```python
# rivaflow/cli/commands/dashboard.py

@app.callback(invoke_without_command=True)
def dashboard(ctx: typer.Context = None):
    """Display today's dashboard with quick actions."""
    user_id = get_current_user_id()
    # ... setup code ...

    # Load all dashboard data at once
    with console.status("[cyan]Loading dashboard...", spinner="dots"):
        today_checkin = checkin_repo.get_checkin(user_id, today)
        checkin_streak = streak_service.get_streak(user_id, "checkin")
        summary = get_week_summary(user_id)
        closest = milestone_service.get_closest_milestone(user_id)

    # Display results (no more database queries)
    # ... display code ...
```

### Engagement Features

```python
# rivaflow/cli/commands/log.py

def _add_engagement_features(session_id: int):
    """Add engagement features after session logging."""
    user_id = get_current_user_id()
    # ... setup code ...

    # Batch expensive operations
    with prompts.console.status("[cyan]Calculating streaks and milestones...", spinner="dots"):
        insight = insight_service.generate_insight(user_id)
        streak_info = streak_service.record_checkin(user_id, "session", today)
        new_milestones = milestone_service.check_all_milestones(user_id)

    # Display results
    # ... display code ...
```

### Export Commands

```python
# rivaflow/cli/app.py

@app.command()
def export(output: Optional[str] = None):
    """Export all your data as JSON."""
    user_id = get_current_user_id()
    # ... setup repositories ...

    with console.status("[cyan]Exporting your data...", spinner="dots"):
        user = user_repo.get_by_id(user_id)
        profile = profile_repo.get_by_user_id(user_id)
        data = {
            "user": user,
            "profile": profile,
            "sessions": session_repo.list_by_user(user_id),
            "readiness": readiness_repo.list_by_user(user_id),
            # ... more collections ...
        }

    # Write to file and display summary
    # ... write code ...
```

### Progress/Stats Commands

```python
# rivaflow/cli/commands/progress.py

@app.callback(invoke_without_command=True)
def progress(ctx: typer.Context):
    """Display lifetime stats and milestone progress."""
    user_id = get_current_user_id()

    # Load stats with spinner
    with console.status("[cyan]Loading lifetime stats...", spinner="dots"):
        stats = get_lifetime_stats(user_id)

    # Display stats table
    # ... display code ...

    # Load milestones with separate spinner
    with console.status("[cyan]Loading milestones...", spinner="dots"):
        achieved = milestone_service.get_all_achieved(user_id)
        progress_list = milestone_service.get_progress_to_next(user_id)
        closest = milestone_service.get_closest_milestone(user_id)

    # Display milestone information
    # ... display code ...
```

## Performance Optimization Tips

### 1. Batch Database Queries

**Before (slow):**
```python
# Multiple sequential queries outside spinner
checkin = checkin_repo.get_checkin(user_id, today)
streak = streak_service.get_streak(user_id, "checkin")
summary = get_week_summary(user_id)
closest = milestone_service.get_closest_milestone(user_id)
```

**After (fast):**
```python
# All queries inside one spinner
with console.status("[cyan]Loading dashboard...", spinner="dots"):
    checkin = checkin_repo.get_checkin(user_id, today)
    streak = streak_service.get_streak(user_id, "checkin")
    summary = get_week_summary(user_id)
    closest = milestone_service.get_closest_milestone(user_id)
```

### 2. Preload Data for Display

Load all required data inside the spinner, then display it afterward:

```python
# Load data (with spinner)
with console.status("[cyan]Loading data...", spinner="dots"):
    data = expensive_load_operation()
    stats = calculate_statistics(data)
    insights = generate_insights(stats)

# Display (no spinner needed - instant)
display_table(stats)
display_insights(insights)
```

### 3. Avoid Nested Spinners

**Bad:**
```python
with console.status("[cyan]Loading part 1..."):
    data1 = load_data_1()

    with console.status("[cyan]Loading part 2..."):  # Nested - confusing
        data2 = load_data_2()
```

**Good:**
```python
with console.status("[cyan]Loading data..."):
    data1 = load_data_1()
    data2 = load_data_2()
```

## Testing Progress Indicators

### Manual Testing

```bash
# Test with actual data volume
rivaflow report month        # Should show spinner for 1-3 seconds
rivaflow progress           # Should show spinner for stats and milestones
rivaflow dashboard          # Should show spinner briefly
rivaflow export             # Should show spinner while collecting data
```

### Performance Expectations

| Command | Expected Time | Spinner Visible? |
|---------|---------------|-----------------|
| `rivaflow report week` | 1-2s | Yes |
| `rivaflow report month` | 2-5s | Yes |
| `rivaflow dashboard` | 0.5-2s | Yes |
| `rivaflow progress` | 1-3s | Yes (twice) |
| `rivaflow export` | 1-3s | Yes |
| `rivaflow log` (after entry) | 1-3s | Yes |

## Accessibility Considerations

1. **Terminal Compatibility**: Rich library automatically handles:
   - No-color terminals (strips formatting)
   - Limited color support (falls back to basic colors)
   - Screen readers (text is still readable)

2. **Message Clarity**: Always provide clear text, not just a spinner:
   ```python
   # Good: Clear message
   with console.status("[cyan]Generating report..."):

   # Bad: Just a spinner, no context
   with console.status(""):
   ```

3. **Non-blocking**: Spinners should not prevent keyboard interrupts (Ctrl+C):
   ```python
   try:
       with console.status("[cyan]Loading..."):
           result = long_operation()
   except KeyboardInterrupt:
       console.print("\n[yellow]Operation cancelled[/yellow]")
       raise typer.Exit(1)
   ```

## Common Patterns

### Pattern 1: Single Long Operation

```python
with console.status("[cyan]Processing...", spinner="dots"):
    result = single_long_operation()
```

### Pattern 2: Multiple Related Operations

```python
with console.status("[cyan]Loading data...", spinner="dots"):
    data1 = operation_1()
    data2 = operation_2()
    data3 = operation_3()
```

### Pattern 3: Sequential Sections

```python
# First section
with console.status("[cyan]Loading stats...", spinner="dots"):
    stats = get_stats()

display_stats(stats)

# Second section
with console.status("[cyan]Loading milestones...", spinner="dots"):
    milestones = get_milestones()

display_milestones(milestones)
```

## Troubleshooting

### Spinner Doesn't Show

**Possible causes:**
1. Operation completes too quickly (<100ms)
2. Console output happens inside the spinner context
3. Exception occurs before spinner starts

**Solution:**
```python
# Move console output outside spinner
with console.status("[cyan]Loading..."):
    data = load_data()

# Display after spinner completes
console.print(data)
```

### Spinner Interferes with Progress Output

**Problem:**
```python
with console.status("[cyan]Loading..."):
    console.print("Step 1")  # Conflicts with spinner
    step1()
    console.print("Step 2")  # Conflicts with spinner
    step2()
```

**Solution:**
```python
# Don't output during spinner
with console.status("[cyan]Processing..."):
    step1()
    step2()

console.print("[green]✓ Complete")
```

### Multiple Spinners in Sequence Feel Slow

**Problem:**
```python
# User sees multiple spinners for related operations
with console.status("[cyan]Loading users..."):
    users = load_users()

with console.status("[cyan]Loading sessions..."):
    sessions = load_sessions()

with console.status("[cyan]Loading stats..."):
    stats = load_stats()
```

**Solution:**
```python
# Combine into one spinner
with console.status("[cyan]Loading data..."):
    users = load_users()
    sessions = load_sessions()
    stats = load_stats()
```

## Rich Library Reference

### Available Spinners

While we use `"dots"` for consistency, Rich supports other spinners:

- `"dots"` - Rotating dots (our standard)
- `"line"` - Rotating line
- `"arc"` - Rotating arc
- `"arrow"` - Rotating arrow
- `"bouncingBar"` - Bouncing bar
- `"moon"` - Moon phases

**Stick to "dots" for consistency across RivaFlow CLI.**

### Color Options

Standard Rich colors used in RivaFlow:
- `[cyan]` - Primary color for progress messages
- `[yellow]` - Warnings
- `[green]` - Success
- `[red]` - Errors

## Related Documentation

- [Rich Library Documentation](https://rich.readthedocs.io/en/stable/progress.html)
- [Color Accessibility Guide](./COLOR_ACCESSIBILITY.md)
- [CLI Branding Guide](./CLI_BRANDING.md)

---

**Last Updated:** 2026-02-02
**Related:** Task #30 from BETA_READINESS_REPORT.md
