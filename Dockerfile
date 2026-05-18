FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
ENV ENVIRONMENT=production
ENV DISABLE_NLP_MODELS=1

RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    gnupg \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.backend.txt .
RUN pip install --no-cache-dir -r requirements.backend.txt

# Install Debian-compatible font packages to work around missing Ubuntu fonts
RUN apt-get update && \
    apt-get install -y fonts-unifont fonts-freefont-ttf && \
    rm -rf /var/lib/apt/lists/*
# Install remaining Playwright system deps (allow failure for Ubuntu-only packages)
RUN playwright install-deps chromium || true
# Install the Chromium browser binary
RUN playwright install chromium

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
