# 🥋 RivaFlow

**Training OS for the mat — Train with intent. Flow to mastery.**

A local-first CLI for logging BJJ/grappling training, tracking readiness, and getting data-driven training suggestions.

## Features

- ⚡ **Fast logging** — Full session in <60 seconds, quick mode in <20
- 📊 **Analytics** — Weekly/monthly reports with submission rates, intensity trends
- 🧠 **Smart suggestions** — Rules-based recommendations (not AI fluff)
- 📹 **Video recall** — Link instructionals to techniques, surface during logging
- 🔒 **Privacy-first** — All data stays on your machine

## Install

```bash
# Recommended: Install with pipx (isolated environment)
pipx install rivaflow

# Alternative: Install with pip
pip install rivaflow
```

## Quick Start

```bash
# Log your first session (interactive)
rivaflow log

# Quick mode: just gym, class type, and rolls
rivaflow log --quick

# Daily readiness check-in
rivaflow readiness

# See your week's stats
rivaflow report week

# Get today's training recommendation
rivaflow suggest
```

## Commands Reference

### Session Logging

```bash
rivaflow log              # Full interactive session logging
rivaflow log --quick      # Quick mode: minimal inputs
```

**Full mode prompts:** class type, gym, location, duration, intensity, rolls (if applicable), submissions, techniques (with video recall cards), partners, notes

**Quick mode prompts:** gym, class type, rolls (if applicable)

### Daily Readiness

```bash
rivaflow readiness                   # Log today's check-in
rivaflow readiness --date 2025-01-20 # Backfill a specific date
```

Tracks: sleep (1-5), stress (1-5), soreness (1-5), energy (1-5), hotspots

### Reports & Analytics

```bash
rivaflow report week                        # Current week (Mon-Sun)
rivaflow report month                       # Current month
rivaflow report range 2025-01-01 2025-01-31 # Custom range

# Export to CSV
rivaflow report week --csv                  # week_report.csv
rivaflow report month --output monthly.csv  # Custom filename
```

**Metrics:** Total classes, hours, rolls, unique partners, submissions (for/against), submission rates, breakdowns by type and gym

### Training Suggestions

```bash
rivaflow suggest           # Get today's recommendation
rivaflow suggest --explain # Verbose mode with all rule explanations
```

**Rules include:**
- High stress/low energy → flow roll or drill-only
- High soreness → recovery day
- Active hotspots → protect injury
- Consecutive Gi/No-Gi → vary stimulus
- Green light → full intensity available
- Stale techniques → revisit what hasn't been trained

### Video Library

```bash
# Add a video
rivaflow video add "https://youtube.com/watch?v=xyz" \
  --title "Danaher Armbar System" \
  --technique "armbar" \
  --timestamps '[{"time":"2:30","label":"entry"},{"time":"5:15","label":"finish"}]'

# List all videos
rivaflow video list

# Filter by technique
rivaflow video list --technique "armbar"

# Search
rivaflow video search "danaher"

# Delete
rivaflow video delete 1 --yes
```

**Recall cards:** When logging techniques with linked videos, recall cards appear showing timestamps and labels.

### Technique Tracking

```bash
rivaflow technique add "armbar" --category submission
rivaflow technique list
rivaflow technique stale          # Not trained in 7+ days
rivaflow technique stale --days 14
rivaflow technique search "arm"
```

### Utilities

```bash
rivaflow init    # Initialize database (runs automatically on first use)
rivaflow stats   # Lifetime statistics
rivaflow export  # Export all data to JSON (rivaflow_export.json)
```

## Data Location

All data stored in `~/.rivaflow/rivaflow.db` (SQLite).

Backup strategy:
```bash
# Export to JSON
rivaflow export

# Or copy database file
cp ~/.rivaflow/rivaflow.db ~/backups/
```

## Supported Class Types

**Sparring:** gi, no-gi, wrestling, judo, open-mat (requires rolls input)
**Non-sparring:** s&c, mobility, yoga, rehab, physio, drilling

## Architecture

Built for future expansion:
- **Pydantic models** → Ready for FastAPI backend
- **Service layer** → Business logic decoupled from CLI
- **Repository pattern** → Easy database migration
- **ISO 8601 dates** → Timezone-portable
- **Local-first** → No cloud dependencies

## Development

```bash
git clone https://github.com/yourusername/rivaflow
cd rivaflow
pip install -e ".[dev]"

# Run locally
python -m rivaflow

# Run tests
pytest

# Lint
ruff check .
```

## Philosophy

RivaFlow is built on these principles:

1. **Fast input** — Logging shouldn't interrupt your flow
2. **Transparent logic** — Rules-based suggestions, not black-box AI
3. **Privacy-first** — Your data stays on your machine
4. **Future-proof** — Architecture ready for web/API version
5. **No fluff** — Just the features that matter for training

## Roadmap

Current version: **v0.1.0 (MVP)**

Future phases:
- Web dashboard (FastAPI + React)
- Team/gym sharing features
- Mobile companion app
- Advanced analytics and visualizations

## License

MIT — See LICENSE file for details

## Contributing

Issues and PRs welcome at https://github.com/yourusername/rivaflow

---

**Train with intent. Flow to mastery.** 🥋
