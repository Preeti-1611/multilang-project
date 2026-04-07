FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY appp.py .
COPY templates/ templates/
COPY static/ static/

ENV PORT=8080
EXPOSE 8080

# Longer timeout: audio upload + STT + translate + TTS
CMD ["sh", "-c", "gunicorn appp:app --bind 0.0.0.0:${PORT:-8080} --workers 2 --timeout 120"]
