FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
    
# Labels
LABEL maintainer="Peter Siebler <peter.siebler@gmail.com>" \
      application="Heizungs Controller Anwendung" \
      version="2.0.0" \
      com.centurylinklabs.watchtower.enable="false" \
      dockerhand.check-update="false"

WORKDIR /app

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendung kopieren
COPY . .

# Verzeichnisse erstellen
RUN mkdir -p data/processed data/raw logs

# Healthcheck
HEALTHCHECK --interval=60s --timeout=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Starten
CMD ["python", "app.py"]
