# Multi-stage production container for Shorts Studio
FROM python:3.11-slim

# Install system dependencies & ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY web/ ./web/
COPY scripts/ ./scripts/
COPY final_clips/ ./final_clips/
COPY credentials/ ./credentials/

# Expose server port
EXPOSE 5050

ENV PORT=5050
ENV PYTHONUNBUFFERED=1

# Run with Gunicorn production server with background Auto-Pilot
CMD ["gunicorn", "--bind", "0.0.0.0:5050", "--workers", "1", "--threads", "4", "--timeout", "120", "web.app:app"]
