# Kokoro-82M with FastAPI
ARG KOKORO_BASE=python:3.10-slim
FROM ${KOKORO_BASE}

WORKDIR /app

# Install system dependencies - handle both Python slim and CUDA base images
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    curl \
    ffmpeg \
    && apt-get install -y --no-install-recommends espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# If using CUDA base image (no Python), install Python
RUN if ! command -v python3 >/dev/null 2>&1; then \
        apt-get update && \
        apt-get install -y --no-install-recommends python3 python3-pip python3-dev && \
        rm -rf /var/lib/apt/lists/*; \
    fi

# Clone Kokoro from GitHub
RUN git clone https://github.com/hexgrad/kokoro.git .

# Copy the FastAPI wrapper from host
COPY kokoro_server.py .

# Install Python dependencies including misaki for English and Chinese
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    python3 -m pip install --no-cache-dir \
    torch \
    numpy \
    scipy \
    soundfile \
    fastapi \
    uvicorn \
    huggingface-hub \
    pydub \
    "kokoro>=0.9.4" \
    "misaki[en,zh]"

# Download the model from Hugging Face
RUN python3 -c "from huggingface_hub import snapshot_download; snapshot_download('hexgrad/Kokoro-82M')"

# Expose the API port
EXPOSE 8880

# Start FastAPI server
CMD ["python3", "-m", "uvicorn", "kokoro_server:app", "--host", "0.0.0.0", "--port", "8880"]
