# Changelog

All notable changes to RivaFlow will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Coming Soon
- Mobile app (iOS/Android)
- Competition tracking and comp prep tools
- Gym/academy management dashboards
- More wearable integrations (Garmin, Apple Watch)

---

## [0.4.0-beta] - 2026-02-08

### Advanced Analytics & Insights Engine

#### Added
- **Insights Tab** — New data-science-driven analytics tab on Reports page
  - ACWR (Acute:Chronic Workload Ratio) training load management with zone bands
  - Readiness x Performance correlation scatter plot with optimal zone detection
  - Technique effectiveness 2x2 quadrant (money moves / developing / natural / untested)
  - Session quality composite scoring (0-100) with weekly trend
  - Overtraining risk gauge (0-100) with factor breakdown and recommendations
  - Recovery insights — sleep-performance correlation and optimal rest day analysis
  - Partner progression tracking — rolling sub rate over time per partner

- **Enhanced Existing Analytics**
  - Training frequency heatmap (GitHub-style calendar) on overview tab
  - Duration analytics — trends, by class type and gym
  - Time-of-day performance patterns
  - Gym comparison analytics
  - Class type effectiveness breakdown
  - Partner belt rank distribution chart
  - Weight trend with 7-day simple moving average

- **Grapple AI Deep Analytics Integration**
  - AI coach now accesses ACWR, overtraining risk, session quality, technique effectiveness, and recovery data
  - Post-session insights enriched with training load and risk context
  - System prompt updated with deep analytics guidelines

- **Pure Python Math Engine** (no numpy dependency)
  - Pearson r correlation
  - Exponentially Weighted Moving Average (EWMA)
  - Shannon entropy for game breadth scoring
  - Linear regression slope for trend detection

- **15 New API Endpoints** under `/api/v1/analytics/`
  - Phase 1: duration/trends, time-of-day/patterns, gyms/comparison, class-types/effectiveness, weight/trend, training-calendar, partners/belt-distribution
  - Phase 2: insights/summary, insights/readiness-correlation, insights/training-load, insights/technique-effectiveness, insights/partner-progression/{id}, insights/session-quality, insights/overtraining-risk, insights/recovery

- **7 New Frontend Visualization Components** (custom SVG, no charting library)
  - ACWRChart, CorrelationScatter, TechniqueQuadrant, QualityTrend, RiskGauge, PartnerProgressionChart, TrainingCalendar

- **Backend Tests** for InsightsAnalyticsService — math helpers and edge cases (30 tests)

- **FAQ Updated** with Insights, Grapple AI, Quick Log, and speech-to-text documentation

---

## [0.3.1-beta] - 2026-02-07

### Session Workflow Overhaul & Quick Log Improvements

#### Added
- **Quick Log** — Auto-creates rolls from selected partners for fast session logging
- **Speech-to-Text** — Microphone input for session notes in Full Log
- **Session Insights** — Post-session AI-generated insights after logging
- **Glossary Unification** — Merged techniques and movements into single unified glossary (migrations 068-069)
- **Grapple AI Coach** — LLM-powered training assistant with full training data context
- **Game Plans** — Structured position flows and drill sequences
- **Social Features** — Groups, friend suggestions, self-friend constraint (migration 070)
- **Signup Onboarding** — Guided first-run experience for new users
- **Error Feedback** — Speech recognition mic button shows errors
- **Timezone Fix** — Session dates correctly localised

#### Fixed
- Session edit bugs (class time, partner linking)
- Partner analytics: active_partners key mismatch and unlinked roll counting
- Technique analytics: use session_techniques table and deduplicate glossary
- Social route tests failing on PostgreSQL (KeyError: 0)
- Grapple AI chat errors: datetime-to-text SQL mismatch and CORS on insight chat
- Grapple rate_limits unique index migration
- SendGrid errors crashing endpoints
- Dark mode text on forgot-password success screen
- Black formatting consistency (line-length=88)

---

## [0.3.0-beta] - 2026-02-01

### 🎉 Beta Release

This release represents a major milestone: RivaFlow is ready for beta testing with comprehensive security improvements, full authentication, and extensive test coverage.

### 🔒 Security & Authentication

#### Added
- **CLI Authentication System** - Full login/logout/register commands
  - Secure credential storage in `~/.rivaflow/credentials.json` (0o600 permissions)
  - `rivaflow auth login` - Login with email/password
  - `rivaflow auth logout` - Logout and remove local credentials
  - `rivaflow auth register` - Create new account
  - `rivaflow auth whoami` - Display current user info
  - Backwards compatible with environment variables for testing

- **Production Security Checks**
  - SECRET_KEY validation (rejects dev keys in production)
  - Minimum 32-character secret key requirement
  - Runtime environment checks

- **Database Security**
  - SQLite database files created with 0o600 permissions (user-only access)
  - Automatic permission enforcement on connection

### 📦 Dependencies & Infrastructure

#### Changed
- **All dependencies pinned to specific versions** for reproducible builds
- Updated to latest stable versions (fastapi 0.128.0, pydantic 2.10.3, etc.)
- Added `pip-audit` to dev dependencies for vulnerability scanning
- Added `pytest-asyncio` for async testing support

### 🧪 Testing

#### Added
- **Authentication Test Suite** (40+ tests)
  - Registration, login, logout flows
  - Password hashing and verification
  - JWT token creation and validation
  - Refresh token management
  - Email validation
  - 100% coverage of authentication critical paths

- **CLI Command Tests** (30+ tests)
  - Session logging validation
  - Rest day logging
  - Readiness check-ins
  - Report generation
  - Input validation and error handling
  - ~60% coverage of CLI commands

- **Integration Tests** (15+ scenarios)
  - End-to-end user journeys
  - Multi-user interactions
  - Data export/import
  - Streak calculation
  - Error recovery scenarios
  - ~70% coverage of integration paths

### 🏗️ Code Quality

#### Added
- **Constants Module** (`rivaflow/core/constants.py`)
  - Centralized configuration values
  - Sort options (SQL injection protection)
  - Visibility levels, class types, belt levels
  - Cache TTL values
  - Validation limits
  - Single source of truth for magic strings

#### Changed
- Updated repositories to use constants from central module
- Improved SQL injection protection with whitelisted sort options

### ⚠️ Known Limitations

This beta release has the following known limitations:

1. **CLI Multi-User Support**: CLI authentication is new - please report any issues
2. **Test Coverage**: Some edge cases may not be fully covered yet
3. **Performance**: Analytics queries not yet optimized for large datasets
4. **Documentation**: Some CLI commands need more detailed examples

### 📝 Fixes & Improvements

#### Fixed
- Profile photo upload now displays correctly in development (Vite proxy fix)
- Session photo upload fully implemented (was placeholder)
- Analytics techniques endpoint error handling improved

#### Changed
- Enhanced error messages throughout API routes
- Improved logging for debugging

---

## [0.2.0] - 2026-01-30

### Features

#### Social Features
- **User Profiles** - View public training profiles
  - Clickable friend activities in feed
  - Avatar photo display
  - Privacy-protected data (email hidden from public profiles)
  - Training stats (sessions, hours, rolls, streaks)
  - Recent activity timeline

- **Friend Following** - Social connections
  - Follow/unfollow users
  - Follower and following counts
  - Mutual follow indicators
  - Social feed with friend activities

#### Session Logging Improvements
- **Rest Day Logging** - Track recovery days
  - QuickLog modal support
  - Full LogSession form with rest day type
  - Types: Active, Passive, Injury, Recovery
  - Optional notes for context

- **Privacy Controls** - Control activity visibility
  - Private, Friends, Public visibility levels
  - Per-session visibility dropdown in feed
  - Optimistic UI updates

#### Analytics Enhancements
- **Quick Date Ranges** - Faster report filtering
  - Last 7 days button
  - Last 14 days button
  - Last 30 days button
  - Custom date range still available

- **Error Handling** - Improved analytics reliability
  - Try-catch blocks on all endpoints
  - Detailed error logging
  - Stack traces for debugging

#### Profile Features
- **Profile Photo Upload** - Personalize your profile
  - Upload from file instead of URL
  - Preview before saving
  - Automatic optimization

### Changes
- Improved readiness check skipping logic
- Better button selectors for class time/duration/intensity
- Enhanced grading with instructor dropdown and photo upload

### Fixes
- Fixed profile photo persistence (Vite proxy configuration)
- Fixed session photo upload "coming soon" error
- Fixed techniques analytics "error loading data" issue

---

## [0.1.0] - 2026-01-15

### Initial Release

#### Core Features
- **Session Logging** - Track BJJ/grappling training
  - Class types (Gi, No-Gi, Wrestling, Judo, etc.)
  - Duration and intensity tracking
  - Roll counting
  - Technique notes
  - Training partner logging

- **Readiness Tracking** - Monitor training readiness
  - Sleep, stress, soreness, energy metrics
  - Weight tracking
  - Hotspot notes for injuries
  - Daily check-ins

- **Analytics & Reports**
  - Weekly summaries
  - Monthly overviews
  - Technique breakdown
  - Training frequency analysis
  - Intensity trends

- **Streak Tracking**
  - Training streaks
  - Readiness check-in streaks
  - Longest streak records
  - Grace period support

- **CLI Interface**
  - `rivaflow log` - Log training sessions
  - `rivaflow readiness` - Log readiness check-in
  - `rivaflow rest` - Log rest days
  - `rivaflow report` - View analytics
  - `rivaflow streak` - View streaks
  - `rivaflow dashboard` - Today's overview

- **Web Interface**
  - Modern React frontend
  - Real-time updates
  - Dark mode support
  - Mobile-responsive design

#### Technical
- **Backend** - FastAPI with Python 3.11+
- **Frontend** - React with TypeScript
- **Database** - Dual support (SQLite/PostgreSQL)
- **Authentication** - JWT tokens with bcrypt password hashing
- **API** - RESTful with automatic OpenAPI docs

---

## Beta Testing Notes

### Reporting Issues

Found a bug? We want to hear about it!

**Via GitHub:**
```
https://github.com/RubyWolff27/rivaflow/issues
```

**Please include:**
- What you were doing
- What you expected to happen
- What actually happened
- Error messages (if any)
- Screenshots (if applicable)

### Known Issues

Track known issues and their status on GitHub:
```
https://github.com/RubyWolff27/rivaflow/issues
```

### Privacy & Data

- Your data stays on your device (SQLite) or your database (PostgreSQL)
- No telemetry or analytics collected
- No data shared with third parties
- Profile data visibility: You control (Private/Friends/Public)

### Feedback Welcome

We're actively working on RivaFlow and value your feedback. Please share:
- Feature requests
- Usability suggestions
- Bug reports
- General thoughts

Thank you for being an early adopter! 🥋

---

## Version History Summary

- **v0.4.0-beta** (2026-02-08) - Advanced analytics & insights engine, Grapple AI deep integration
- **v0.3.1-beta** (2026-02-07) - Session workflow overhaul, Quick Log, Grapple AI, Game Plans
- **v0.3.0-beta** (2026-02-01) - Beta release with security & testing
- **v0.2.0** (2026-01-30) - Social features & analytics improvements
- **v0.1.0** (2026-01-15) - Initial release

[unreleased]: https://github.com/RubyWolff27/rivaflow/compare/v0.4.0-beta...HEAD
[0.4.0-beta]: https://github.com/RubyWolff27/rivaflow/compare/v0.3.1-beta...v0.4.0-beta
[0.3.1-beta]: https://github.com/RubyWolff27/rivaflow/compare/v0.3.0-beta...v0.3.1-beta
[0.3.0-beta]: https://github.com/RubyWolff27/rivaflow/compare/v0.2.0...v0.3.0-beta
[0.2.0]: https://github.com/RubyWolff27/rivaflow/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/RubyWolff27/rivaflow/releases/tag/v0.1.0
