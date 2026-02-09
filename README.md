# 🥋 RivaFlow

**Training OS for the mat — Train with intent. Flow to mastery.**

A local-first training tracker for BJJ/grappling with both **CLI** and **Web App** interfaces.

## Features

- ⚡ **Fast logging** — Full session in <60 seconds, quick mode in <20
- 👥 **Contacts management** — Track instructors and training partners with belt ranks and certifications
- 📚 **BJJ Glossary** — 82 pre-loaded techniques across 8 categories (positions, submissions, sweeps, passes, takedowns, escapes, movements, concepts)
- 🎯 **Detailed roll tracking** — Log individual rolls with partner, submissions from glossary, duration, and notes
- 🔄 **Flexible entry modes** — Simple mode (quick totals) or Detailed mode (roll-by-roll analytics)
- 📊 **Advanced Analytics** — ACWR training load, overtraining risk, technique quadrants, session quality, recovery insights
- 🤖 **Grapple AI Coach** — LLM-powered coaching with deep training data context
- 🗺️ **Game Plans** — Structured position flows and drill sequences
- 🎙️ **Speech-to-Text** — Voice input for session notes
- 📹 **Video recall** — Link instructionals to techniques, surface during logging
- 🎯 **Monthly Goals** — User-defined monthly training goals with auto-tracked progress
- ⌚ **WHOOP Integration** — Connect your WHOOP band for strain, HR, calorie overlay, recovery-aware AI coaching, and sport science analytics (recovery-performance correlation, strain efficiency, HRV predictor, sleep impact, cardiovascular drift)
- 🔒 **Privacy-first** — Granular privacy controls (private/attendance/summary/full)

## Install

### Prerequisites

- **Python 3.11 or later** (check with `python --version`)
- **Node.js 18 or later** (for web app, check with `node --version`)
- **Git** (for cloning the repository)
- **PostgreSQL** (optional for production, SQLite used for local development)

### Installation Steps

```bash
# Clone the repository
git clone https://github.com/RubyWolff27/rivaflow
cd rivaflow

# Install Python dependencies
pip install -e .

# For web app, also install Node.js dependencies
cd web && npm install && cd ..
```

**Note:** On first run, the database will be initialized automatically. Your data will be stored in `~/.rivaflow/`

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
- **Insights** — ACWR training load, overtraining risk (6 factors incl. WHOOP HRV/recovery), technique quadrants, session quality, recovery analysis
- **Performance Science** — WHOOP-powered sport analytics: recovery-performance correlation, strain efficiency, HRV predictor, sleep impact, cardiovascular drift
- **Grapple AI** — Chat with AI coach powered by your training data
- **Game Plans** — Build and review position flow charts
- **Monthly Goals** — Set and auto-track frequency and technique goals each month
- **WHOOP Sync** — Connect WHOOP band, overlay strain/HR/calories, recovery context per session, Performance Science charts
- **Profile** — Manage your information, default gym, belt progression, and WHOOP connection

See [WEB_README.md](WEB_README.md) for full web app documentation.

## 💻 CLI Usage

### First Time Setup

**Create your account:**
```bash
rivaflow auth register
# Prompts for: email, first name, last name, password
```

**Or login to existing account:**
```bash
rivaflow auth login
# Prompts for: email, password
```

**Check who's logged in:**
```bash
rivaflow auth whoami
```

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

**Example Session:**
```bash
$ rivaflow log
Class type: gi
Gym: Gracie Barra
Location: Los Angeles
Duration (minutes) [60]: 90
Intensity (1-5) [4]: 5
Number of rolls: 8
Submissions scored: armbar, triangle
Training partners: John, Sarah
Notes: Great flow rolling session. Worked on passing guard.
✓ Session logged successfully!
```

**With command-line flags:**
```bash
rivaflow log --gym "Gracie Barra" --duration 90 --intensity 5 --class-type gi
```

### Daily Readiness

```bash
rivaflow readiness                   # Log today's check-in
rivaflow readiness --date 2025-01-20 # Backfill a specific date
```

Tracks: sleep (1-5), stress (1-5), soreness (1-5), energy (1-5), hotspots

**Example Check-in:**
```bash
$ rivaflow readiness
How did you sleep? (1-5): 4
Stress level? (1-5): 2
Soreness? (1-5): 3
Energy level? (1-5): 4
Any injury hotspots? (optional): left shoulder
✓ Readiness logged

Readiness Score: 13/20 (65%)
Status: Good to train - moderate intensity recommended
```

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

**Example Weekly Report:**
```bash
$ rivaflow report week
Week of Jan 27 - Feb 2, 2026

Training Volume
  Classes:         5
  Total Hours:     7.5
  Total Rolls:     42
  Unique Partners: 8

Performance
  Submissions For:     12
  Submissions Against: 8
  Submission Rate:     60%

By Class Type
  Gi:      3 classes (4.5 hrs)
  No-Gi:   2 classes (3.0 hrs)

By Gym
  Gracie Barra:    3 classes
  10th Planet:     2 classes

Consistency
  Training Days:   5/7 (71%)
  Rest Days:       2
  Avg Intensity:   4.2/5
```

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

### Authentication & Account

```bash
# Register new account
rivaflow auth register
# Prompts: email, first name, last name, password (min 8 chars)

# Login
rivaflow auth login
# Prompts: email, password

# Check current user
rivaflow auth whoami
# Shows: name, email, user ID

# Logout
rivaflow auth logout
```

**Example:**
```bash
$ rivaflow auth register
Email: john@example.com
First name: John
Last name: Doe
Password (min 8 characters): ********
Confirm password: ********
✓ Account created successfully!
  Welcome to RivaFlow, John!
  Your account email: john@example.com
```

### Rest Days & Recovery

```bash
# Log a rest day
rivaflow rest
# Prompts: type (active/passive/injury), optional note

# With flags
rivaflow rest --type injury --note "Shoulder rehab"

# Log rest day for specific date
rivaflow rest --date 2026-01-31 --type active
```

**Example:**
```bash
$ rivaflow rest
Rest day type (active/passive/injury): active
Note (optional): Light yoga and stretching
✓ Rest day logged successfully
```

### Engagement Commands

```bash
# Today's dashboard
rivaflow dashboard
# Shows: greeting, week summary, streaks, tomorrow's plan

# View streaks
rivaflow streak
# Shows: current training/readiness/check-in streaks

# Track progress
rivaflow progress
# Shows: weekly progress, milestones, achievements

# Plan tomorrow
rivaflow tomorrow
# Set intention: train_gi, train_nogi, rest, etc.
```

**Example Dashboard:**
```bash
$ rivaflow dashboard
Good morning! 🥋

This Week
  Sessions:    3
  Hours:       4.5
  Rolls:       24
  Rest Days:   1

Current Streaks
  Training:    3 days 🔥
  Readiness:   7 days ⚡
```

### Data Export & Privacy

```bash
# Export all your data (GDPR compliant)
rivaflow export
# Creates: rivaflow_export_<user_id>_<date>.json

# Export to specific file
rivaflow export --output my_backup.json

# Delete account (permanent!)
rivaflow delete-account --confirm
# Triple confirmation: yes/no prompt + email verification
```

**Export includes:** sessions, readiness entries, techniques, videos, gradings, friends, profile data

### Utilities

```bash
rivaflow init    # Initialize database (runs automatically on first use)
rivaflow stats   # Lifetime statistics
rivaflow --help  # See all commands
rivaflow <command> --help  # Help for specific command
```

**Example Stats:**
```bash
$ rivaflow stats
RivaFlow Lifetime Stats

  Total Sessions        147
  Total Hours           220.5
  Total Rolls           1,234
  Readiness Entries     203
  Techniques Tracked    42
  Videos Saved          18
```

## Data Location

All data stored locally in `~/.rivaflow/`:

- `rivaflow.db` - SQLite database with all your training data
- `credentials.json` - Encrypted login credentials (0o600 permissions)
- `.welcomed` - First-run marker

**Backup strategy:**
```bash
# Option 1: Export to JSON (recommended)
rivaflow export --output ~/backups/rivaflow_$(date +%Y%m%d).json

# Option 2: Copy database file
cp ~/.rivaflow/rivaflow.db ~/backups/

# Option 3: Full directory backup
cp -r ~/.rivaflow ~/backups/rivaflow_backup_$(date +%Y%m%d)
```

**Restore from backup:**
```bash
# Restore database
cp ~/backups/rivaflow.db ~/.rivaflow/

# Or restore full directory
cp -r ~/backups/rivaflow_backup_20260201 ~/.rivaflow
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

Current version: **v0.5.0-beta**

**Completed:**
- ✅ CLI tool with session logging, readiness tracking, and reports
- ✅ Web dashboard (FastAPI + React)
- ✅ Quick Log and Full Log with speech-to-text
- ✅ Unified BJJ glossary with 82+ techniques
- ✅ Detailed roll tracking with partner-specific analytics
- ✅ Advanced analytics & insights engine (ACWR, risk, quality, recovery)
- ✅ Grapple AI Coach with deep analytics integration
- ✅ Game Plans with position flows and drill sequences
- ✅ Social features (groups, friends, feed, likes, comments)
- ✅ Profile management with belt progression history
- ✅ Monthly training goals with auto-tracked progress
- ✅ WHOOP wearable integration (OAuth, workout sync, biometric overlay, recovery sync, sport science analytics, recovery-aware AI)

**Upcoming:**
- Mobile companion app (iOS/Android)
- Competition tracking and comp prep tools
- Gym/academy management dashboards
- More wearable integrations (Garmin, Apple Watch)

## 🧪 Beta Status

RivaFlow is currently in **beta testing** (v0.5.0-beta). Here's what to expect:

**Working Well:**
- ✅ Multi-user authentication (CLI and web)
- ✅ Session logging with detailed roll tracking
- ✅ Readiness tracking and smart suggestions
- ✅ Weekly/monthly reports and analytics
- ✅ Training streaks and milestone tracking
- ✅ Social feed (share sessions with friends)
- ✅ Profile and belt progression tracking
- ✅ GDPR-compliant data export and account deletion

**Known Limitations:**
- ⚠️ **Test Coverage:** Some edge cases may not be fully covered
- ⚠️ **Performance:** Analytics queries not yet optimized for large datasets (>1000 sessions)
- 📌 **Data Storage:** PostgreSQL in production, SQLite for local development

**Reporting Issues:**
- **Web App:** Click "Give Feedback" button (beta banner)
- **GitHub:** Create issue at [github.com/RubyWolff27/rivaflow/issues](https://github.com/RubyWolff27/rivaflow/issues)
- **Include:** What you were doing, what you expected, what happened, error messages

**Data Privacy:**
- ✅ All data encrypted at rest (database permissions: 0o600)
- ✅ You control visibility (private, friends-only, or public)
- ✅ Export your data anytime: `rivaflow export` (CLI) or Settings → Export (Web)
- ✅ Delete account: `rivaflow delete-account` (permanent deletion with confirmation)

## Troubleshooting

### Common Issues

**"Not logged in" error when running commands:**
```bash
# Solution: Login first
rivaflow auth login

# Or register if you're new
rivaflow auth register
```

**"Invalid email or password":**
```bash
# Check your credentials
rivaflow auth whoami  # See if you're logged in

# If you forgot password, delete credentials and re-register
rm ~/.rivaflow/credentials.json
rivaflow auth register
```

**Database errors or corrupted data:**
```bash
# Option 1: Export data and reinitialize
rivaflow export --output backup.json
rm ~/.rivaflow/rivaflow.db
rivaflow init

# Option 2: Restore from backup
cp ~/backups/rivaflow.db ~/.rivaflow/
```

**Command not found: rivaflow:**
```bash
# Reinstall package
pip install -e .

# Or run directly
python -m rivaflow.cli.app
```

**Permission denied errors:**
```bash
# Fix database permissions
chmod 600 ~/.rivaflow/rivaflow.db
chmod 600 ~/.rivaflow/credentials.json
```

**Web app won't start:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Restart both services
./start-web.sh

# Or start separately
uvicorn rivaflow.api.main:app --reload --port 8000  # Backend
cd web && npm run dev  # Frontend
```

**Import errors:**
```bash
# Reinstall dependencies
pip install -e ".[dev]"

# For web app
cd web && npm install
```

### Getting Help

1. **Check the logs:**
   ```bash
   # CLI errors show in terminal
   rivaflow --help

   # Web app logs
   tail -f ~/.rivaflow/logs/app.log  # If logging configured
   ```

2. **Search existing issues:**
   - GitHub: https://github.com/RubyWolff27/rivaflow/issues

3. **Create a new issue:**
   - Include: OS, Python version, error message, steps to reproduce
   - Run: `python --version` and `rivaflow --version`

4. **Debug mode:**
   ```bash
   # Enable verbose logging
   export RIVAFLOW_DEBUG=1
   rivaflow log
   ```

## License

MIT — See LICENSE file for details

## Contributing

Issues and PRs welcome at https://github.com/RubyWolff27/rivaflow

---

**Train with intent. Flow to mastery.** 🥋
