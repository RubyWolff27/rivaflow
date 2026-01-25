"""FastAPI application for RivaFlow web interface."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rivaflow.api.routes import sessions, readiness, reports, suggestions, techniques, videos, profile, gradings, glossary, contacts, analytics, goals

app = FastAPI(
    title="RivaFlow API",
    description="Training OS for the mat — Web API",
    version="0.1.0",
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(readiness.router, prefix="/api/readiness", tags=["readiness"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(suggestions.router, prefix="/api/suggestions", tags=["suggestions"])
app.include_router(techniques.router, prefix="/api/techniques", tags=["techniques"])
app.include_router(videos.router, prefix="/api/videos", tags=["videos"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(gradings.router, prefix="/api/gradings", tags=["gradings"])
app.include_router(glossary.router, prefix="/api/glossary", tags=["glossary"])
app.include_router(contacts.router, prefix="/api/contacts", tags=["contacts"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(goals.router, prefix="/api/goals", tags=["goals"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "RivaFlow API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
