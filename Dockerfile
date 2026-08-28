FROM python:3.11-slim-bookworm

WORKDIR /app

# System deps for psycopg2 + Playwright's Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright browser binaries (needed for tools/scraper.py's JS fallback)
RUN playwright install --with-deps chromium

COPY . .

# Default command runs the one-off pipeline; override in docker-compose
# for the scheduler (celery beat/worker) and dashboard (streamlit) services.
CMD ["python", "-m", "pipeline.graph"]
