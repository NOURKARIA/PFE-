FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    gnupg \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download en_core_web_sm
RUN playwright install --with-deps chromium

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]