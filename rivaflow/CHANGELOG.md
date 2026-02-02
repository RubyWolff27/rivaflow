# Changelog

All notable changes to RivaFlow will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive README.md with installation, quick start, and feature documentation
- LICENSE file (MIT)
- CHANGELOG.md (this file)
- BETA_READINESS_REPORT.md with comprehensive pre-release audit

### Fixed
- PostgreSQL compatibility for datetime field handling across all repositories
- Session validation to handle empty strings from frontend forms
- SendGrid email error handling with SMTP fallback
- Password reset token validation for PostgreSQL datetime objects
- Validation error logging now includes detailed error messages
- Photo upload PostgreSQL compatibility in ActivityPhotoRepository
- Chat session PostgreSQL compatibility

### Security
- Enhanced SendGrid error handling with detailed 403 diagnostics
- Password reset flow improvements
- Token security verified

## [0.2.0] - 2026-02-01

### Added
- Social features (following, followers, activity feed)
- Photo uploads for sessions
- Session navigation (previous/next)
- Photo thumbnails in activity feed (Strava/IG style)
- Notifications system
- Activity likes and comments
- User profiles with following/follower counts

### Changed
- Improved feed service with photo integration
- Enhanced session service with navigation support

### Fixed
- Database migration compatibility issues
- Various PostgreSQL/SQLite compatibility issues
- Feed service query optimizations

## [0.1.0] - 2026-01-25

### Added
- CLI interface with Typer
- Web API with FastAPI
- Session logging (gi, no-gi, drilling, wrestling, etc.)
- Readiness tracking (sleep, stress, soreness, energy)
- Training analytics and reports
- Goals and streaks
- Belt progression tracking
- Technique library with videos
- AI training insights (Grapple chat)
- Privacy controls (private/attendance/summary/full)
- GDPR compliance (data export and account deletion)
- Multi-database support (SQLite and PostgreSQL)
- Email service with SendGrid/SMTP
- Authentication (JWT-based)
- User management
- Dashboard views
- First-run welcome experience

### Security
- Bcrypt password hashing
- Parameterized SQL queries
- JWT token authentication
- Secure password reset flow
- File permission controls (600 for database)

## Release History

### Beta Phases

#### Phase 1: Core Features (v0.1.0)
- Session logging
- Analytics
- Goals/streaks
- CLI interface

#### Phase 2: Social & Engagement (v0.2.0)
- Following/followers
- Activity feed
- Likes and comments
- Notifications
- Photo uploads

#### Phase 3: Beta Hardening (Upcoming)
- Comprehensive test coverage (>80%)
- Rate limiting on auth endpoints
- CSRF protection
- Enhanced security
- Performance optimizations
- User documentation

### Versioning Strategy

- **Major version (X.0.0):** Breaking changes, major architectural changes
- **Minor version (0.X.0):** New features, backwards-compatible
- **Patch version (0.0.X):** Bug fixes, security patches

### Upgrade Notes

#### Upgrading to 0.2.0

- Database migrations required: Run `python rivaflow/db/migrate.py`
- New environment variables optional:
  - `SENDGRID_API_KEY` for email features
  - `REDIS_URL` for caching (optional)
- PostgreSQL users: Recent fixes improve compatibility

#### Upgrading to 0.1.0

- Initial release, no upgrade path

---

## Contributing

Please read [CONTRIBUTING.md](./CONTRIBUTING.md) for details on our process for submitting pull requests.

## Links

- [GitHub Repository](https://github.com/yourusername/rivaflow)
- [Documentation](./docs/)
- [Issue Tracker](https://github.com/yourusername/rivaflow/issues)

---

**Legend:**
- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` in case of vulnerabilities
