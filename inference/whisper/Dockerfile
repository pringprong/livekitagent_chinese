# syntax=docker/dockerfile:1.5
ARG WHISPER_BASE=python:3.10-slim
FROM ${WHISPER_BASE}

ENV PIP_DISABLE_PIP_VERSION_CHECK=1

RUN --mount=type=cache,id=whisper,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=whisper,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    python3-setuptools \
    && if ! command -v python3 >/dev/null 2>&1; then \
        apt-get install -y --no-install-recommends python3 python3-pip; \
    fi \
    && if ! command -v pip3 >/dev/null 2>&1; then \
        apt-get install -y --no-install-recommends python3-pip; \
    fi \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,id=whisper,target=/root/.cache/pip \
    --mount=type=cache,id=whisper-hf,target=/root/.cache/huggingface \
    python3 -m pip install --upgrade pip "setuptools<82.0.0" wheel \
    && python3 -m pip install --no-build-isolation vox-box

WORKDIR /app

ENV DATA_DIR=/data

CMD ["sh", "-c", "vox-box start --huggingface-repo-id ${VOXBOX_HF_REPO_ID:-Systran/faster-whisper-large-v3} --data-dir ${DATA_DIR} --device ${VOXBOX_DEVICE:-cpu}"]
