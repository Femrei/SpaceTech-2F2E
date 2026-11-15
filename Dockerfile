# Earth Trend Detective: one container serving the 3D detective app (detective3d/).
#   docker build -t earth-trend-detective .
#   docker run -p 8000:8000 earth-trend-detective      ->  http://localhost:8000
# Hosting platforms (Render, Hugging Face Spaces, Railway …) set $PORT; we honour it.
#
# The chat agent needs an LLM key to answer freely; set it as a secret environment
# variable on the host (never in the image), e.g. LLM_PROVIDER=groq + LLM_API_KEY=...
# Without a key the chat runs in offline (rule-based) mode and everything else works.
#
# The React UI in frontend/ is kept in the repo but no longer built or served here.

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000 HOST=0.0.0.0
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# agent_server.py imports api.py (which imports power_loader.py) and src/
COPY api.py power_loader.py ./
COPY src/ src/
COPY data/ data/
COPY detective3d/ detective3d/
EXPOSE 8000
CMD ["python", "detective3d/agent_server.py"]
