# CLI Help Text and Examples Guide

## Overview

All RivaFlow CLI commands include comprehensive help text with real-world examples to guide users.

## Accessing Help

View help for any command:
```bash
rivaflow --help                    # Main help
rivaflow log --help                # Command-specific help
rivaflow report week --help        # Subcommand help
```

## Enhanced Commands

### rivaflow log

**Description:** Log a training session with detailed tracking

**Modes:**
- Quick mode (`--quick`): Fast logging with minimal prompts
- Full mode (default): Complete session with partners, techniques, notes

**Examples:**
```bash
# Quick log (2-3 prompts)
rivaflow log --quick
rivaflow log -q

# Full detailed session
rivaflow log
```

**Help output:**
```
$ rivaflow log --help

QUICK MODE (--quick):
  Fast session logging with minimal prompts.
  Great for logging on the go.

FULL MODE (default):
  Complete session tracking with:
  • Partners and rolls
  • Submissions for/against
  • Techniques learned
  • Notes and reflections
```

---

### rivaflow readiness

**Description:** Log daily readiness check-in to monitor recovery

**Metrics tracked:**
- Sleep quality (1-5)
- Stress level (1-5)
- Muscle soreness (1-5)
- Energy level (1-5)
- Body weight (optional)
- Injury/hotspot notes (optional)

**Examples:**
```bash
# Log today's readiness
rivaflow readiness

# Log for a specific date
rivaflow readiness --date 2026-02-01
rivaflow readiness -d 2026-02-01
```

---

### rivaflow report week

**Description:** Show current week training report (Monday-Sunday)

**Displays:**
- Total sessions and hours
- Average intensity
- Rolls and submissions
- Class type breakdown
- Daily session list

**Examples:**
```bash
# View week report
rivaflow report week

# Export to CSV
rivaflow report week --csv
rivaflow report week --output my_week.csv
```

---

### rivaflow report month

**Description:** Show current month training report

**Includes:**
- Training volume and trends
- Performance metrics
- Weekly comparison
- Top techniques

**Examples:**
```bash
# View month report
rivaflow report month

# Export month data
rivaflow report month --csv
```

---

### rivaflow report range

**Description:** Show training report for custom date range

**Use cases:**
- Belt promotion periods
- Training camps
- Competition prep cycles
- Injury recovery periods

**Examples:**
```bash
# Last 30 days
rivaflow report range 2026-01-03 2026-02-02

# Competition prep (3 months)
rivaflow report range 2025-11-01 2026-02-01

# Export belt period
rivaflow report range 2025-06-01 2025-12-31 --csv
```

---

### rivaflow rest

**Description:** Log a rest/recovery day to maintain check-in streak

**Rest types:**
- `recovery` - Planned rest for recovery (default)
- `life` - Life got in the way
- `injury` - Recovering from injury
- `travel` - Traveling or away from gym

**Examples:**
```bash
# Quick recovery day
rivaflow rest

# Injury rest with note
rivaflow rest --type injury --note "Sore shoulder"
rivaflow rest -t injury -n "Knee tweak"

# Travel day with tomorrow's intention
rivaflow rest -t travel --tomorrow "Back to training!"
```

---

## Help Text Best Practices

### Formatting Standards

1. **Use `\b` blocks** - Preserves formatting in Typer
   ```python
   """
   Command description.

   \b
   Section Header:
     • Bullet point 1
     • Bullet point 2
   """
   ```

2. **Examples section** - Always include real examples
   ```python
   """
   \b
   Examples:
     # Comment explaining use case
     $ command with arguments
   ```

3. **Section structure** - Consistent order
   - Description
   - Features/Options (if complex)
   - Examples
   - Related commands (if applicable)

### Writing Guidelines

**Do:**
- Use active voice ("Log a session" not "Logs a session")
- Include realistic examples
- Explain what vs how (what it does, how to use it)
- Show both short and long option forms (`-d` and `--date`)
- Add comments in examples to explain use cases

**Don't:**
- Use jargon without explanation
- Make examples too complex
- Assume prior knowledge
- Repeat information from option help
- Use placeholder values ("foo", "bar")

### Example Template

```python
@app.command()
def example(
    required: str = typer.Argument(..., help="Required value"),
    flag: bool = typer.Option(False, "--flag", "-f", help="Enable feature"),
):
    """
    Brief one-line description of what this command does.

    \b
    Detailed explanation:
      • Key feature 1
      • Key feature 2
      • Key feature 3

    \b
    Examples:
      # Basic usage
      $ rivaflow command value

      # With optional flag
      $ rivaflow command value --flag
      $ rivaflow command value -f

      # Complex scenario
      $ rivaflow command "special value" --flag
    """
```

## Command Help Quick Reference

| Command | Purpose | Key Examples |
|---------|---------|--------------|
| `log` | Log training session | `rivaflow log --quick` |
| `readiness` | Daily check-in | `rivaflow readiness` |
| `rest` | Log rest day | `rivaflow rest -t injury` |
| `report week` | Weekly summary | `rivaflow report week --csv` |
| `report month` | Monthly summary | `rivaflow report month` |
| `report range` | Custom period | `rivaflow report range 2026-01-01 2026-02-01` |
| `streak` | View streaks | `rivaflow streak` |
| `dashboard` | Today's overview | `rivaflow` (no args) |
| `about` | Version info | `rivaflow about` |

## User Feedback Integration

Help text should evolve based on:
- Common user questions
- Frequent support requests
- Usage patterns
- Onboarding feedback

Review and update help text quarterly to ensure it remains useful and accurate.

---

**Last Updated:** 2026-02-02
**Related:** Task #35 from BETA_READINESS_REPORT.md
