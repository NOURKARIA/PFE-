# Deployment

## Recommended Architecture

Deploy the project as two separate services:

- **Railway:** FastAPI backend, Playwright execution, OCR, YOLO fallback, and report generation.
- **Streamlit Community Cloud:** lightweight UI that calls the Railway backend through `BACKEND_URL`.

This separation avoids the resource-limit problem that happens when Streamlit Cloud tries to run browser automation and AI inference directly.

## 1. Railway Backend

Create a Railway service from the GitHub repository and let Railway detect the root `Dockerfile`.

The Dockerfile uses:

- `requirements.backend.txt` for backend dependencies;
- Playwright Chromium for browser automation;
- Tesseract OCR for text extraction;
- YOLO/Ultralytics for visual fallback;
- `DISABLE_NLP_MODELS=1` by default to avoid loading large NLP `.pt` files during cloud startup. The API still uses the rule-based fallback, which is enough for deployment demos.

Required Railway settings:

```text
Health check path: /health
Start command: empty
Port: automatic, Railway injects PORT
```

The container command already uses Railway's port:

```text
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

After deployment, copy the public Railway URL:

```text
https://your-service-name.up.railway.app
```

Test the backend:

```text
https://your-service-name.up.railway.app/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "Smart Searcher AI Agent",
  "environment": "production"
}
```

## 2. Streamlit Cloud Frontend

Deploy `streamlit_app.py` on Streamlit Community Cloud from the same GitHub repository.

The root `requirements.txt` is intentionally lightweight:

```text
streamlit==1.41.1
httpx==0.27.2
```

In Streamlit Cloud, open **App settings > Secrets** and add:

```toml
BACKEND_URL = "https://your-service-name.up.railway.app"
```

Then reboot the Streamlit app. The Status page should display the backend URL and the health check should pass.

## 3. Local Mode

If `BACKEND_URL` is not set, `streamlit_app.py` falls back to importing the local FastAPI backend. This mode is useful for development, but it requires the backend dependencies and Playwright browsers to be installed locally.
