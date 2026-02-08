# RivaFlow 🥋

**Training OS for the Mat** — Local-first BJJ training tracker with CLI and web interface

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](./tests/)

Train with intent. Flow to mastery.

---

## What is RivaFlow?

RivaFlow is a comprehensive training tracker built specifically for Brazilian Jiu-Jitsu and grappling athletes. Track sessions, analyze progress, build streaks, and gain AI-powered insights to optimize your training journey.

### Key Features

- 📊 **Session Logging** — Track gi, no-gi, drilling, wrestling, and more with Quick Log or Full Log
- 📈 **Advanced Analytics** — ACWR training load, overtraining risk, technique quadrants, session quality scoring
- 🧠 **Insights Engine** — Readiness-performance correlation, recovery analysis, partner progression tracking
- 🤖 **Grapple AI Coach** — Chat with AI powered by your deep training analytics
- 🎯 **Goals & Streaks** — Set weekly goals, track training consistency
- 🏆 **Belt Progression** — Log gradings and track rank history
- 💪 **Readiness Tracking** — Monitor sleep, stress, soreness, energy with performance correlation
- 🎥 **Technique Library** — Unified glossary with video references
- 🗺️ **Game Plans** — Structured position flows and drill sequences
- 👥 **Social Features** — Follow training partners, groups, share sessions, activity feed
- 🎙️ **Speech-to-Text** — Voice input for session notes
- 🔒 **Privacy First** — Local-first with granular privacy controls
- 🌐 **Dual Interface** — CLI for power users, web app for everyone

---

## Quick Start

### Installation

```bash
# From PyPI (when published)
pip install rivaflow

# From source
git clone https://github.com/RubyWolff27/rivaflow.git
cd rivaflow
pip install -e .
```

### First Run

```bash
# Register an account
rivaflow auth register

# Log your first session
rivaflow log

# View your dashboard
rivaflow
```

That's it! You're tracking training in 30 seconds.

---

## CLI Usage

### Core Commands

```bash
# Dashboard (default command)
rivaflow                        # Show today's dashboard

# Session Logging
rivaflow log                    # Log a training session (interactive)
rivaflow log --date 2024-01-15  # Log session for specific date
rivaflow rest                   # Log a rest day

# Readiness Check-ins
rivaflow readiness              # Log daily readiness (sleep, stress, soreness, energy)

# Reports & Analytics
rivaflow report week            # Weekly training report
rivaflow report month           # Monthly training report
rivaflow stats                  # Lifetime statistics

# Streaks & Progress
rivaflow streak                 # View training streaks
rivaflow progress               # View progress toward goals

# Techniques
rivaflow technique add          # Add technique to library
rivaflow technique list         # List all techniques
rivaflow video add              # Save technique video reference

# Data Export
rivaflow export                 # Export all data as JSON (GDPR compliant)
rivaflow delete-account         # Delete account and all data
```

### Authentication

```bash
rivaflow auth register          # Create new account
rivaflow auth login             # Login to existing account
rivaflow auth logout            # Logout
rivaflow auth forgot-password   # Request password reset
```

### Get Help

```bash
rivaflow --help                 # See all commands
rivaflow log --help             # Help for specific command
```

---

## Web API

### Run the API Server

```bash
# Development
uvicorn rivaflow.api.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn rivaflow.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### API Documentation

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Key Endpoints

```bash
# Authentication
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh

# Sessions
GET    /api/v1/sessions/
POST   /api/v1/sessions/
GET    /api/v1/sessions/{id}
PUT    /api/v1/sessions/{id}
DELETE /api/v1/sessions/{id}

# Analytics
GET    /api/v1/analytics/dashboard
GET    /api/v1/analytics/techniques/breakdown

# Social
GET    /api/v1/feed/
POST   /api/v1/social/follow/{user_id}
POST   /api/v1/activities/{activity_type}/{activity_id}/like

# AI Chat (Grapple)
POST   /api/v1/grapple/chat
GET    /api/v1/grapple/sessions/
```

---

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/rivaflow  # or sqlite:///path/to/db

# Authentication
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# Email (for password reset)
SENDGRID_API_KEY=your-sendgrid-key
FROM_EMAIL=noreply@rivaflow.com
# OR use SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# AI Features (optional)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379

# App
APP_BASE_URL=https://rivaflow.onrender.com
ENV=production  # or development
```

Create a `.env` file in the project root (see `.env.example`).

---

## Features in Detail

### Session Logging

Track every aspect of your training:

- **Class Types:** Gi, No-Gi, Wrestling, Judo, Open Mat, Drilling, S&C, Mobility, Yoga
- **Metrics:** Duration, intensity (1-5), number of rolls
- **Performance:** Submissions for/against, partners, techniques practiced
- **Notes:** Freeform text for insights and observations
- **Wearable Integration:** Whoop strain, calories, HR data

### Privacy Controls

Granular privacy settings for social sharing:

- **Private:** Hidden from everyone
- **Attendance:** Shows you trained, but no details
- **Summary:** Shows stats (rolls, duration) but not specifics
- **Full:** Everything is visible

### Analytics & Insights

Comprehensive reports and deep analytics:

- **Standard Analytics** — Training volume, submission rates, technique breakdown, partner stats, streaks
- **Training Calendar** — GitHub-style heatmap of your activity
- **ACWR Training Load** — Acute:Chronic Workload Ratio with zone bands (undertrained / sweet spot / caution / danger)
- **Overtraining Risk** — Composite score (0-100) from ACWR spikes, readiness decline, hotspots, intensity creep
- **Technique Quadrants** — Money moves, developing, natural talent, untested (via Shannon entropy)
- **Session Quality** — Composite scoring (intensity + submissions + techniques + volume)
- **Recovery Insights** — Sleep-performance correlation, optimal rest day analysis
- **Partner Progression** — Rolling sub rate trends against specific partners
- **Gym & Class Type Comparison** — Performance breakdown across gyms and session types
- **Time-of-Day Patterns** — Best training windows based on your data

### AI Training Assistant (Grapple)

Chat with AI about your training:

```bash
"What should I focus on this week?"
"How's my triangle choke progression?"
"Why am I getting submitted more in no-gi?"
"Suggest drills for half guard retention"
```

Grapple analyses your training history, ACWR load, overtraining risk, technique effectiveness, and recovery patterns to provide personalised coaching insights. Post-session insights are automatically generated after logging.

---

## Development

### Project Structure

```
rivaflow/
├── cli/              # CLI commands and utilities
├── api/              # FastAPI web application
├── core/             # Business logic and services
├── db/               # Database layer and repositories
├── tests/            # Test suite
├── docs/             # User documentation
└── deployment/       # Deployment configs
```

### Run Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=rivaflow --cov-report=html

# Specific test file
pytest tests/unit/test_goals_service.py
```

### Code Quality

```bash
# Linting
ruff check .

# Formatting
black .

# Type checking
mypy rivaflow/ --ignore-missing-imports
```

### Database Migrations

```bash
# Initialize database
python -c "from rivaflow.db.database import init_db; init_db()"

# Run migrations
python rivaflow/db/migrate.py
```

---

## Deployment

### Deploy to Render.com

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for detailed instructions.

Quick version:

```bash
# Set environment variables in Render dashboard
# Deploy from GitHub (auto-deploy on push)
# Database: PostgreSQL addon
# Start command: python rivaflow/db/migrate.py && uvicorn rivaflow.api.main:app --host 0.0.0.0 --port $PORT
```

### Docker

```bash
# Build
docker build -t rivaflow .

# Run
docker run -p 8000:8000 --env-file .env rivaflow
```

---

## Data Privacy & GDPR

RivaFlow is **GDPR-compliant** and respects your data rights:

- ✅ **Right to Access:** Export all your data anytime (`rivaflow export`)
- ✅ **Right to Erasure:** Delete your account and all data (`rivaflow delete-account`)
- ✅ **Privacy by Design:** Local-first, granular sharing controls
- ✅ **No Analytics:** We don't track you
- ✅ **No Selling Data:** Your training data is yours

---

## Roadmap

### Current Version (v0.4.0-beta)

- ✅ Session logging (all class types) with Quick Log and Full Log
- ✅ Advanced analytics & insights engine (ACWR, risk, quality, recovery)
- ✅ Grapple AI Coach with deep analytics integration
- ✅ Game Plans with position flows and drill sequences
- ✅ Goals, streaks, and milestones
- ✅ Social features (following, groups, feed, likes, comments)
- ✅ Unified technique glossary with video references
- ✅ Belt progression tracking
- ✅ Privacy controls (private/attendance/summary/full)
- ✅ Speech-to-text for session notes
- ✅ Post-session AI-generated insights
- ✅ Web + CLI interfaces

### Coming Soon

- [ ] Mobile app (iOS/Android)
- [ ] Competition tracking and comp prep tools
- [ ] Gym/academy management dashboards
- [ ] More wearable integrations (Garmin, Apple Watch)
- [ ] Video analysis integration

---

## FAQ

### Is my data safe?

Yes. Your training data is stored securely with:
- Bcrypt password hashing
- Parameterized SQL queries (SQL injection proof)
- Owner-only file permissions
- Optional local-only mode (CLI only, no cloud)

### Can I use this offline?

Yes! The CLI works completely offline with a local SQLite database. The web interface requires internet for deployment, but your data can be exported anytime.

### How much does it cost?

RivaFlow is **free and open-source** (MIT License). You can self-host for $0/month, or use our hosted version (pricing TBD).

### What if I have questions?

- 📧 Email: support@rivaflow.com
- 💬 Discord: [Coming soon]
- 🐛 GitHub Issues: [Report bugs](https://github.com/RubyWolff27/rivaflow/issues)

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

Quick contribution workflow:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## License

MIT License - see [LICENSE](./LICENSE) for details.

---

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
- [Pydantic](https://pydantic.dev/) - Data validation

Inspired by the BJJ community's dedication to continuous improvement.

---

## Support the Project

If RivaFlow helps your training:

- ⭐ Star this repo
- 🐛 Report bugs
- 💡 Suggest features
- 🤝 Contribute code
- 📣 Share with training partners

Train with intent. Flow to mastery. 🥋

---

**Made with ❤️ by grapplers, for grapplers.**
