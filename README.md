# 🥋 RivaFlow

**Training OS for the mat — Train with intent. Flow to mastery.**

A local-first training tracker for BJJ/grappling with both **CLI** and **Web App** interfaces.

## Features

- ⚡ **Fast logging** — Full session in <60 seconds, quick mode in <20
- 👥 **Contacts management** — Track instructors and training partners with belt ranks and certifications
- 📚 **BJJ Glossary** — 82 pre-loaded techniques across 8 categories (positions, submissions, sweeps, passes, takedowns, escapes, movements, concepts)
- 🎯 **Detailed roll tracking** — Log individual rolls with partner, submissions from glossary, duration, and notes
- 🔄 **Flexible entry modes** — Simple mode (quick totals) or Detailed mode (roll-by-roll analytics)
- 📊 **Analytics** — Weekly/monthly reports with submission rates, intensity trends, partner-specific stats
- 🧠 **Smart suggestions** — Rules-based recommendations (not AI fluff)
- 📹 **Video recall** — Link instructionals to techniques, surface during logging
- 🔒 **Privacy-first** — All data stays on your machine

## Install

```bash
# Clone the repository
git clone https://github.com/RubyWolff27/rivaflow
cd rivaflow

# Install Python dependencies
pip install -e .

# For web app, also install Node.js dependencies
cd web && npm install && cd ..
```

## 🌐 Web App (NEW!)

**Modern web interface that works on computer and mobile:**

```bash
# Start both backend and frontend
./start-web.sh

# Then open http://localhost:5173 in your browser
```

### Web App Features

- **Dashboard** — Quick overview of recent sessions, readiness trends, and statistics
- **Session Logging** — 2-step wizard with readiness check-in and comprehensive session details
- **Contacts** — Manage instructors and training partners with belt ranks, stripes, and certifications
- **Glossary** — Browse, search, and filter 82 BJJ techniques by category and gi/no-gi applicability
- **Detailed Roll Tracking** — Log individual rolls with partner selection and submission tracking from glossary
- **Reports** — Weekly/monthly analytics with breakdown by class type and gym
- **Profile** — Manage your information, default gym, and belt progression history

See [WEB_README.md](WEB_README.md) for full web app documentation.

## 💻 CLI Usage

> **⚠️ IMPORTANT:** The CLI currently supports **single-user mode only** (defaults to user_id=1).
> For multi-user accounts, please use the **Web App** interface.
> Multi-user CLI authentication is planned for v0.2.

## Quick Start Examples

**After training:**
```bash
# Log your session
rivaflow log

# You'll be prompted for:
# - Class type (gi, no-gi, wrestling, etc.)
# - Gym name (autocompletes from history)
# - Duration, intensity (1-5)
# - Number of rolls (for sparring classes)
# - Submissions, partners, techniques
# - Notes
```

**Morning routine:**
```bash
# Check your readiness
rivaflow readiness

# Prompts for:
# - Sleep quality (1-5)
# - Stress level (1-5)
# - Soreness (1-5)
# - Energy (1-5)
# - Injury hotspots

# Get training recommendation
rivaflow suggest

# Example output:
# ✓ GREEN LIGHT - Full training available
# or
# ⚠ YELLOW LIGHT - Consider flow rolling (high stress detected)
```

**Weekly review:**
```bash
# See your week's stats
rivaflow report week

# Shows:
# - Total classes, hours, rolls
# - Submissions for/against
# - Breakdown by class type and gym
# - Unique training partners
```

## CLI Command Reference

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
git clone https://github.com/RubyWolff27/rivaflow
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

Current version: **v0.2.0**

**Completed:**
- ✅ CLI tool with session logging, readiness tracking, and reports
- ✅ Web dashboard (FastAPI + React)
- ✅ Contacts management with belt rank tracking
- ✅ BJJ glossary with 82 techniques
- ✅ Detailed roll tracking with partner-specific analytics
- ✅ Profile management with belt progression history

**Upcoming:**
- Partner analytics dashboard (submission rates, roll stats by partner)
- Technique heatmaps and progression tracking
- Team/gym sharing features
- Mobile companion app
- Advanced visualizations and trend analysis

## 🧪 Beta Status

RivaFlow is currently in **beta testing**. Here's what to expect:

**Working Well:**
- ✅ Session logging (CLI and web)
- ✅ Readiness tracking and suggestions
- ✅ Weekly/monthly reports and analytics
- ✅ Training streaks and goals
- ✅ Social feed (share sessions with friends)
- ✅ Profile and belt progression tracking

**Known Limitations:**
- ⚠️ **CLI Authentication:** Single-user only (use web app for multi-user)
- ⚠️ **Photo Upload:** UI exists but backend in development
- 📌 **Data Storage:** PostgreSQL in production, SQLite for local development

**Reporting Issues:**
- **Web App:** Click "Give Feedback" button (beta banner)
- **GitHub:** Create issue at [github.com/RubyWolff27/rivaflow/issues](https://github.com/RubyWolff27/rivaflow/issues)
- **Email:** support@rivaflow.com (if configured)

**Data Privacy:**
- All session data stored securely
- You control visibility (private, friends-only, or public)
- Export your data anytime: `rivaflow export` (CLI) or Settings → Export (Web)

## License

MIT — See LICENSE file for details

## Contributing

Issues and PRs welcome at https://github.com/RubyWolff27/rivaflow

---

**Train with intent. Flow to mastery.** 🥋
