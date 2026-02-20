FROM python:3.11-slim

# Install system dependencies for psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer caching)
COPY rivaflow/requirements.txt rivaflow/requirements.txt
RUN pip install --no-cache-dir -r rivaflow/requirements.txt

# Copy application code
COPY rivaflow/ rivaflow/
COPY start.sh start.sh

# Create non-root user for running the app
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Default port
ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["bash", "start.sh"]
