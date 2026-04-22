# Kokoro-82M with FastAPI
ARG KOKORO_BASE=python:3.10-slim
FROM ${KOKORO_BASE}

WORKDIR /app

# Install system dependencies - handle both Python slim and CUDA base images
RUN --mount=type=cache,id=kokoro,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=kokoro,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    curl \
    ffmpeg \
    && apt-get install -y --no-install-recommends espeak-ng 

# If using CUDA base image (no Python), install Python
RUN if ! command -v python3 >/dev/null 2>&1; then \
        apt-get update && \
        apt-get install -y --no-install-recommends python3 python3-pip python3-dev && \
        rm -rf /var/lib/apt/lists/*; \
    fi

# Clone Kokoro from GitHub with network-resilient retries
RUN --mount=type=cache,id=kokoro-git,target=/root/.cache/git \
    git config --global http.lowSpeedLimit 0 && \
    git config --global http.lowSpeedTime 999999 && \
    for i in 1 2 3 4 5; do \
      git clone --depth 1 --shallow-submodules https://github.com/hexgrad/kokoro.git . && break; \
      echo "git clone failed, retrying (\50/5)"; \
      sleep 5; \
    done

# Copy the FastAPI wrapper from host
COPY kokoro_server.py .

# Install Python dependencies including misaki for English and Chinese
RUN --mount=type=cache,id=kokoro,target=/root/.cache/pip \
    python3 -m pip install --upgrade pip setuptools wheel && \
    python3 -m pip install \
    torch \
    numpy \
    scipy \
    soundfile \
    fastapi \
    uvicorn \
    huggingface-hub \
    pydub \
    "kokoro>=0.9.4" \
    "misaki[en,zh]" \
    --resume-retries 20

# Download spacy language model for offline use
RUN python3 -m spacy download en_core_web_sm

# Download the model from Hugging Face and prepare offline cache
RUN --mount=type=cache,id=kokoro,target=/root/.cache/huggingface \
    HF_HUB_OFFLINE=0 python3 -c "from huggingface_hub import snapshot_download; snapshot_download('hexgrad/Kokoro-82M')" && \
    ls -la /root/.cache/huggingface/hub/ 2>/dev/null || echo "No cached models found"

# Set environment variables for offline mode
ENV HF_HUB_DISABLE_PROGRESS_BARS=1
ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1

# Expose the API port
EXPOSE 8880

# Run the server
CMD ["python3", "kokoro_server.py"]
