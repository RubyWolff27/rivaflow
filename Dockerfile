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

# Default port
ENV PORT=8000
EXPOSE 8000

CMD ["bash", "start.sh"]
