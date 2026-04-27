# 1. Use a lightweight Python base image
FROM python:3.10-slim

# 2. Set environment variables (Fixed format)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# 3. Set the working directory
WORKDIR /app

# 4. Install system dependencies (Fixed for Debian Trixie)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    libtesseract-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*


# 5. Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Download the spaCy model (English small)
RUN python -m spacy download en_core_web_sm

# 7. Install Playwright browsers and their system dependencies
RUN playwright install --with-deps chromium

# 8. Copy the rest of the application code
COPY . .

# 9. Expose the port FastAPI runs on
EXPOSE 8000

# 10. Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]