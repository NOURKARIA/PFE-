# Deployment

## Recommended Setup

Deploy the heavy FastAPI automation backend on Railway with Docker, then deploy the lightweight Streamlit UI on Streamlit Cloud.

## 1. Railway Backend

Create a Railway project from this repository. Railway should use the root `Dockerfile`.

The Dockerfile installs `requirements.backend.txt`, Playwright Chromium, Tesseract, spaCy, and the AI/CV dependencies.

Required settings:

- Health check path: `/health`
- Start command: leave empty, because the Dockerfile already defines it
- Port: Railway injects `PORT`; the Dockerfile command uses `${PORT:-8000}`

After deploy, copy your Railway public URL. It will look like:

```text
https://your-service-name.up.railway.app
```

Test:

```text
https://your-service-name.up.railway.app/health
```

## 2. Streamlit UI

Deploy `streamlit_app.py` to Streamlit Cloud from the same repository.

The root `requirements.txt` is intentionally light:

```text
streamlit
httpx
```

In Streamlit Cloud, add this secret or environment variable:

```toml
BACKEND_URL = "https://your-service-name.up.railway.app"
```

Then reboot the Streamlit app.

## Local Mode

If `BACKEND_URL` is not set, `streamlit_app.py` falls back to importing the local FastAPI app and running the pipeline on your machine.
