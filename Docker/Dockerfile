# Use a lightweight image
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV HF_HOME=/app/models

# Install system dependencies only once
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies separately for better caching
COPY requirements.txt .

# Use pip cache for faster rebuilds
RUN python -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Now copy your app
COPY . .

# Expose port and run gunicorn
EXPOSE 8001

ENV PATH="/opt/venv/bin:$PATH"
CMD ["gunicorn", "app.main:app", "-c", "gunicorn_conf.py"]
