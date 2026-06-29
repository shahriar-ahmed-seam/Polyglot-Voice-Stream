# Backend container for Render / Railway / Fly.io (NOT Vercel).
FROM python:3.10-slim

WORKDIR /app

# CPU-only torch + torchaudio (silero-vad needs torchaudio; the default PyPI
# build is CUDA-enabled and fails on CPU hosts with a missing libcudart).
RUN pip install --no-cache-dir torch==2.3.1 torchaudio==2.3.1 \
    --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY server.py .

# Hosts inject $PORT; default to 8000 locally.
ENV PORT=8000
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT}"]
