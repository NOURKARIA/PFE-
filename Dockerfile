FROM python:3.10-slim-bookworm

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

RUN playwright install --with-deps chromium

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
