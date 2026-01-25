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
pipx install rivaflow
```

## Quick Start
```bash
# Log your first session
rivaflow log

# Check in daily
rivaflow readiness

# See your week
rivaflow report week

# Get training advice
rivaflow suggest
```

## Data Location

All data stored in `~/.rivaflow/rivaflow.db` (SQLite).

## Development

```bash
git clone https://github.com/yourusername/rivaflow
cd rivaflow
pip install -e ".[dev]"
```

## License

MIT
