# Configuration Management Guide

## Overview

RivaFlow uses centralized configuration management through the `settings` module, providing a single source of truth for all application settings, environment variables, and runtime configuration.

## Architecture

### Settings Module (`rivaflow/core/settings.py`)

The `Settings` class provides type-safe access to all configuration values with:
- Environment variable loading with defaults
- Property-based access (lazy loading)
- Type conversion and validation
- Feature flags
- Environment detection helpers

### Constants Module (`rivaflow/core/constants.py`)

Static application constants that don't change at runtime:
- Class types and belt levels
- Sort options (SQL injection protection)
- Activity types
- Validation limits
- Milestone thresholds

### Config Module (`rivaflow/config.py`)

**DEPRECATED** - Maintained for backwards compatibility only.
New code should use `rivaflow.core.settings` instead.

## Usage

### Importing Settings

```python
from rivaflow.core.settings import settings

# Access configuration
secret_key = settings.SECRET_KEY
is_prod = settings.IS_PRODUCTION
db_url = settings.DATABASE_URL
```

### Environment Detection

```python
from rivaflow.core.settings import settings

# Check environment
if settings.IS_PRODUCTION:
    # Production-specific code
    pass

if settings.IS_DEVELOPMENT:
    # Development-specific code
    pass

if settings.IS_TEST:
    # Test-specific code
    pass
```

### Feature Flags

```python
from rivaflow.core.settings import settings

# Check feature flags
if settings.ENABLE_GRAPPLE:
    # Enable AI coaching features
    pass

if settings.ENABLE_SOCIAL_FEATURES:
    # Enable likes, comments, friends
    pass
```

### Database Configuration

```python
from rivaflow.core.settings import settings

# Database access
db_url = settings.DATABASE_URL
db_type = settings.DB_TYPE  # "sqlite" or "postgresql"
db_path = settings.DB_PATH  # For SQLite

if settings.DB_TYPE == "postgresql":
    # PostgreSQL-specific logic
    pass
```

### Email Configuration

```python
from rivaflow.core.settings import settings

# Email settings
if settings.SENDGRID_API_KEY:
    # Use SendGrid
    pass
elif settings.SMTP_USER:
    # Use SMTP
    pass

from_email = settings.FROM_EMAIL
from_name = settings.FROM_NAME
```

### File Uploads

```python
from rivaflow.core.settings import settings

max_size = settings.MAX_UPLOAD_SIZE_BYTES
upload_dir = settings.UPLOAD_DIR
```

### Rate Limiting

```python
from rivaflow.core.settings import settings

if settings.RATE_LIMIT_ENABLED:
    limit_per_min = settings.RATE_LIMIT_PER_MINUTE
    limit_per_hour = settings.RATE_LIMIT_PER_HOUR
```

## Environment Variables

### Required Variables

These must be set in all environments:

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key (>= 32 chars) | `python -c 'import secrets; print(secrets.token_urlsafe(32))'` |

### Database Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | SQLite | PostgreSQL URL: `postgresql://user:pass@host:port/db` |

### Authentication Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Refresh token lifetime |

### Email Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SENDGRID_API_KEY` | None | SendGrid API key |
| `SMTP_HOST` | `smtp.gmail.com` | SMTP server |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` | None | SMTP username |
| `SMTP_PASSWORD` | None | SMTP password |
| `FROM_EMAIL` | SMTP_USER | Sender email |
| `FROM_NAME` | `RivaFlow` | Sender name |

### Application URLs

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_BASE_URL` | `https://rivaflow.onrender.com` | App base URL |
| `API_BASE_URL` | APP_BASE_URL | API base URL |

### Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_GRAPPLE` | `true` | AI coaching features |
| `ENABLE_WHOOP_INTEGRATION` | `false` | WHOOP integration |
| `ENABLE_SOCIAL_FEATURES` | `true` | Social features |

### AI/LLM Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | None | Groq API key |
| `TOGETHER_API_KEY` | None | Together AI key |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server |

### Caching Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379` | Redis connection |
| `CACHE_ENABLED` | `false` | Enable caching |

### Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_ENABLED` | `true` | Enable rate limits |
| `RATE_LIMIT_PER_MINUTE` | `60` | Max requests/minute |
| `RATE_LIMIT_PER_HOUR` | `1000` | Max requests/hour |

### File Uploads

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_UPLOAD_SIZE_MB` | `10` | Max file size (MB) |
| `UPLOAD_DIR` | `~/.rivaflow/uploads` | Upload directory |

### Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | `development` | Environment name |
| `LOG_LEVEL` | `INFO` (prod) / `DEBUG` (dev) | Log level |
| `LOG_FILE` | None | Log file path |

### CORS

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:8000` | Allowed origins |

## Environment Files

### Development (.env)

```bash
# Required
SECRET_KEY=your-dev-secret-key-minimum-32-characters-long

# Optional Development Settings
ENV=development
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///~/.rivaflow/rivaflow.db

# Feature Flags (Optional)
ENABLE_GRAPPLE=true
ENABLE_SOCIAL_FEATURES=true
```

### Production (Render, etc.)

```bash
# Required
SECRET_KEY=<generated-secret-key>
DATABASE_URL=postgresql://user:pass@host:port/db

# Environment
ENV=production
LOG_LEVEL=INFO

# Email (Choose one)
SENDGRID_API_KEY=<your-sendgrid-key>
# OR
SMTP_USER=<your-email>
SMTP_PASSWORD=<your-password>

# Application URLs
APP_BASE_URL=https://your-domain.com

# Feature Flags
ENABLE_GRAPPLE=true
ENABLE_WHOOP_INTEGRATION=false
ENABLE_SOCIAL_FEATURES=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

### Testing

```bash
# Required
SECRET_KEY=test-secret-key-for-testing-purposes-minimum-32-chars

# Test Environment
ENV=test
DATABASE_URL=sqlite:///:memory:
LOG_LEVEL=WARNING
```

## Migration Guide

### Old Pattern (Deprecated)

```python
import os
from rivaflow.config import DB_PATH, DEFAULT_DURATION

# Direct os.getenv access
api_key = os.getenv("GROQ_API_KEY")
```

### New Pattern (Recommended)

```python
from rivaflow.core.settings import settings
from rivaflow.core.constants import DEFAULT_SESSION_DURATION

# Use settings instance
api_key = settings.GROQ_API_KEY
duration = DEFAULT_SESSION_DURATION
```

## Best Practices

### DO:

✅ Use `settings` for runtime configuration
```python
from rivaflow.core.settings import settings
db_url = settings.DATABASE_URL
```

✅ Use `constants` for static values
```python
from rivaflow.core.constants import MIN_PASSWORD_LENGTH
```

✅ Check feature flags before using features
```python
if settings.ENABLE_GRAPPLE:
    # Use Grapple features
```

✅ Use environment detection
```python
if settings.IS_PRODUCTION:
    # Production-specific behavior
```

### DON'T:

❌ Access environment variables directly
```python
import os
api_key = os.getenv("API_KEY")  # Bad
```

❌ Hardcode configuration values
```python
max_size = 10 * 1024 * 1024  # Bad
```

❌ Import from deprecated config module
```python
from rivaflow.config import DB_PATH  # Deprecated
```

## Testing

Override settings in tests:

```python
import os
from rivaflow.core.settings import settings

def test_production_behavior():
    # Override environment
    os.environ["ENV"] = "production"

    # Settings will reflect change
    assert settings.IS_PRODUCTION == True

    # Cleanup
    del os.environ["ENV"]
```

## Debugging

View all settings:

```python
from rivaflow.core.settings import settings

# Export settings (omits sensitive values)
config_dict = settings.as_dict()
print(config_dict)
```

## Security Notes

1. **Never commit `.env` files** - Add to `.gitignore`
2. **Use strong SECRET_KEY** - Minimum 32 characters
3. **Rotate secrets regularly** - Update production keys periodically
4. **Validate production config** - Settings class validates on access
5. **Use environment-specific values** - Different keys for dev/prod

---

**Last Updated:** 2026-02-02
**Related:** Task #27 from BETA_READINESS_REPORT.md
