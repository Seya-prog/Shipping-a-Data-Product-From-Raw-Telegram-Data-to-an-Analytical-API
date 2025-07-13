# ------------------------------
# Dockerfile for Telegram Data Product Pipeline
# ------------------------------
# Base lightweight Python image
FROM python:3.11-slim

# Prevent prompts
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies (if any needed for psycopg2 etc.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Default command (can be overridden by docker-compose)
CMD ["python", "-m", "pip", "--version"]
