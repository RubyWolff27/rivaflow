"""FastAPI application for RivaFlow web interface."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

try:
    import sentry_sdk

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.gzip import GZipMiddleware

from rivaflow.api.middleware.error_handler import (
    generic_exception_handler,
    rivaflow_exception_handler,
    validation_exception_handler,
)
from rivaflow.api.middleware.request_id import RequestIDMiddleware
from rivaflow.api.middleware.request_logging import RequestLoggingMiddleware
from rivaflow.api.middleware.request_size import RequestSizeLimitMiddleware
from rivaflow.api.middleware.security_headers import SecurityHeadersMiddleware
from rivaflow.api.middleware.versioning import VersioningMiddleware
from rivaflow.api.routes import (
    admin,
    admin_broadcast,
    admin_grapple,
    admin_gyms,
    admin_users,
    analytics,
    auth,
    checkins,
    coach_preferences,
    dashboard,
    events,
    feed,
    feedback,
    friends,
    game_plans,
    glossary,
    goals,
    gradings,
    grapple,
    grapple_insights,
    grapple_usage,
    groups,
    gyms,
    health,
    integrations,
    milestones,
    notifications,
    photos,
    profile,
    readiness,
    reports,
    rest,
    sessions,
    social,
    social_comments,
    social_connections,
    social_likes,
    streaks,
    suggestions,
    techniques,
    training_goals,
    transcribe,
    users,
    videos,
    waitlist,
    webhooks,
)
from rivaflow.core.exceptions import RivaFlowException
from rivaflow.core.settings import settings

# Read version from single source of truth
_VERSION_FILE = Path(__file__).parent.parent / "VERSION"
_APP_VERSION = _VERSION_FILE.read_text().strip() if _VERSION_FILE.exists() else "0.5.0"

# Configure logging — JSON in production, plain text elsewhere
if settings.IS_PRODUCTION:
    try:
        from pythonjsonlogger.json import JsonFormatter

        _handler = logging.StreamHandler()
        _handler.setFormatter(
            JsonFormatter(
                fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )
        logging.root.handlers = [_handler]
        logging.root.setLevel(logging.INFO)
    except ImportError:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

# Initialize Sentry error tracking (only if SDK installed and DSN configured)
_sentry_dsn = os.getenv("SENTRY_DSN")
if SENTRY_AVAILABLE and _sentry_dsn:
    sentry_sdk.init(
        dsn=_sentry_dsn,
        environment=os.getenv("ENV", "development"),
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        send_default_pii=False,
    )
    logging.info("Sentry error tracking initialized")

# Initialize rate limiter (disabled in test environment)
from rivaflow.api.rate_limit import _get_real_client_ip  # noqa: E402

if not settings.IS_TEST:
    limiter = Limiter(key_func=_get_real_client_ip)
else:
    from slowapi import Limiter as DummyLimiter

    limiter = DummyLimiter(key_func=_get_real_client_ip, enabled=False)

_docs_url = None if settings.IS_PRODUCTION else "/docs"
_redoc_url = None if settings.IS_PRODUCTION else "/redoc"
_openapi_url = None if settings.IS_PRODUCTION else "/openapi.json"


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    """Manage application startup and shutdown."""
    # --- Startup ---
    from rivaflow.core.config_validator import validate_environment

    validate_environment()

    # Ensure upload directory exists
    settings.ensure_upload_dir()

    # Seed glossary on every startup to pick up new terms.
    try:
        from rivaflow.db.seed_glossary import seed_glossary

        seed_glossary()
    except (OSError, ConnectionError, ValueError) as e:
        logging.warning(f"Could not seed glossary: {e}")

    # Backfill session scores for any unscored sessions (idempotent).
    if not settings.IS_TEST:
        try:
            logging.info("Starting session score backfill...")
            from rivaflow.db.backfill_scores import backfill_all_users

            backfill_all_users()
            logging.info("Session score backfill complete.")
        except Exception:
            logging.warning("Session score backfill failed", exc_info=True)

    if not settings.IS_TEST:
        try:
            from rivaflow.core.scheduler import start_scheduler

            start_scheduler()
        except Exception as e:
            logging.warning(f"Background scheduler failed to start: {e}")

    yield

    # --- Shutdown ---
    from rivaflow.db.database import close_connection_pool

    close_connection_pool()

    try:
        from rivaflow.core.scheduler import stop_scheduler

        stop_scheduler()
    except Exception:
        pass


app = FastAPI(
    title="RivaFlow API",
    description="Training OS for the mat — Web API",
    version=_APP_VERSION,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
    lifespan=_lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter
if not settings.IS_TEST:
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Register custom error handlers
app.add_exception_handler(RivaFlowException, rivaflow_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# CORS configuration - use settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "OPTIONS",
    ],  # Restrict to necessary methods
    allow_headers=["Content-Type", "Authorization"],  # Only allow necessary headers
    expose_headers=[
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "Retry-After",
    ],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Add versioning middleware for backward compatibility
app.add_middleware(VersioningMiddleware)

# Add gzip compression for responses > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add security headers for production hardening
app.add_middleware(SecurityHeadersMiddleware)

# Add request ID tracking
app.add_middleware(RequestIDMiddleware)

# Add request logging (method, path, status, latency)
app.add_middleware(RequestLoggingMiddleware)

# Add request body size limit (10MB)
app.add_middleware(RequestSizeLimitMiddleware)


# Register health check routes (no prefix for easy access by load balancers)
app.include_router(health.router)

# Register routes with /api/v1/ prefix
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(readiness.router, prefix="/api/v1/readiness", tags=["readiness"])
app.include_router(rest.router, prefix="/api/v1")
app.include_router(feed.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(
    suggestions.router, prefix="/api/v1/suggestions", tags=["suggestions"]
)
app.include_router(techniques.router, prefix="/api/v1/techniques", tags=["techniques"])
app.include_router(videos.router, prefix="/api/v1/videos", tags=["videos"])
app.include_router(profile.router, prefix="/api/v1/profile", tags=["profile"])
app.include_router(gradings.router, prefix="/api/v1/gradings", tags=["gradings"])
app.include_router(glossary.router, prefix="/api/v1/glossary", tags=["glossary"])
app.include_router(friends.router, prefix="/api/v1/friends", tags=["friends"])
app.include_router(groups.router, prefix="/api/v1/groups", tags=["groups"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(goals.router, prefix="/api/v1/goals", tags=["goals"])
app.include_router(
    training_goals.router,
    prefix="/api/v1/training-goals",
    tags=["training-goals"],
)
app.include_router(
    coach_preferences.router,
    prefix="/api/v1/coach-preferences",
    tags=["coach-preferences"],
)
app.include_router(checkins.router, prefix="/api/v1")
app.include_router(streaks.router, prefix="/api/v1")
app.include_router(milestones.router, prefix="/api/v1")
app.include_router(photos.router, prefix="/api/v1")
app.include_router(social.router, prefix="/api/v1")
app.include_router(social_likes.router, prefix="/api/v1/social", tags=["social"])
app.include_router(social_comments.router, prefix="/api/v1/social", tags=["social"])
app.include_router(social_connections.router, prefix="/api/v1/social", tags=["social"])
# AI features (Grapple + Game Plans)
app.include_router(grapple.router, prefix="/api/v1")
app.include_router(grapple_insights.router, prefix="/api/v1/grapple", tags=["grapple"])
app.include_router(grapple_usage.router, prefix="/api/v1/grapple", tags=["grapple"])
app.include_router(game_plans.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(admin_gyms.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(admin_users.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(admin_broadcast.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(admin_grapple.router, prefix="/api/v1")
app.include_router(gyms.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(transcribe.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(integrations.router, prefix="/api/v1", tags=["integrations"])
app.include_router(webhooks.router, prefix="/api/v1", tags=["webhooks"])
app.include_router(waitlist.router, prefix="/api/v1/waitlist", tags=["waitlist"])
app.include_router(
    waitlist.admin_router, prefix="/api/v1/admin/waitlist", tags=["admin-waitlist"]
)


# Serve uploaded files locally (only when S3 is not configured)
if not os.getenv("S3_BUCKET_NAME"):
    uploads_path = Path(__file__).parent.parent.parent / "uploads"
    uploads_path.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

# Serve static files from the React build (for production)
# This allows serving both API and frontend from the same domain
web_dist_path = Path(__file__).parent.parent.parent / "web" / "dist"
if web_dist_path.exists():
    # Mount static assets (JS, CSS, images, etc.)
    app.mount(
        "/assets", StaticFiles(directory=str(web_dist_path / "assets")), name="assets"
    )

    # Catch-all route to serve index.html for React Router
    # This must be defined last to not override other routes
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        """Serve the React app for all non-API routes."""
        # Don't intercept API routes or health check
        if (
            full_path.startswith("api/")
            or full_path.startswith("api/v1/")
            or full_path == "health"
        ):
            return {"error": "Not found"}

        # Serve index.html for all other routes (React Router will handle routing)
        index_file = web_dist_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        else:
            return {"error": "Frontend not built. Run 'cd web && npm run build'"}

else:
    # If frontend not built, show API info at root
    @app.get("/")
    async def root():
        """Root endpoint when frontend is not available."""
        return {
            "message": "RivaFlow API",
            "version": _APP_VERSION,
            "docs": "/docs",
        }
