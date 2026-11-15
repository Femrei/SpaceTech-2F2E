# Earth Trend Detective: one container serving the FastAPI backend and the built React UI.
#   docker build -t earth-trend-detective .
#   docker run -p 8000:8000 earth-trend-detective      ->  http://localhost:8000
# Hosting platforms (Render, Hugging Face Spaces, Railway …) set $PORT; we honour it.

# --- 1) Build the React frontend -------------------------------------------
FROM node:22-slim AS web
# Override if the default npm registry is unreachable from your network, e.g.
#   docker build --build-arg NPM_REGISTRY=https://registry.yarnpkg.com/ .
ARG NPM_REGISTRY=https://registry.npmjs.org/
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund --registry=$NPM_REGISTRY
COPY frontend/ ./
RUN npm run build

# --- 2) Python runtime: API + static frontend ------------------------------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api.py power_loader.py ./
COPY src/ src/
COPY data/ data/
# No processed CSV yet (A's real data not committed)? Fall back to B's mock data
# so the app still starts; the UI then shows a "synthetic data" warning.
RUN [ -f data/processed/all_series.csv ] || python -m src.mock_data
COPY --from=web /app/frontend/dist frontend/dist
EXPOSE 8000
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT}"]
