Read [](file:///c%3A/Users/pring/local-voice-ai/livekit_agent)

Read [](file:///c%3A/Users/pring/local-voice-ai/livekit_agent/src/agent.py#1-1), lines 1 to 100

Read [](file:///c%3A/Users/pring/local-voice-ai/livekit_agent/README.md#1-1), lines 1 to 50

Read [](file:///c%3A/Users/pring/local-voice-ai/livekit_agent/src/agent.py#100-100), lines 100 to 117

Read [](file:///c%3A/Users/pring/local-voice-ai/frontend/components)

Read [](file:///c%3A/Users/pring/local-voice-ai/frontend/app/layout.tsx#1-1), lines 1 to 50

## Comprehensive App Overview

### **Components**

The app is a modular, containerized voice AI system with these services:

1. **LiveKit Server** (livekit)
   - WebRTC signaling server for real-time audio/video communication
   - Manages rooms and enables peer connections between browser clients and the agent

2. **LiveKit Agents Server** (livekit_agent)
   - Python backend orchestrating the STT → LLM → TTS pipeline
   - Uses the LiveKit Agents SDK to integrate with various models
   - Includes voice activity detection (VAD) via Silero
   - Preemptive generation for lower latency
   - Supports function tools (you can add custom functions like `multiply_numbers` in the example)

3. **Speech-to-Text (STT)** — Two Options:
   - **Nemotron** (default) — NVIDIA's speech streaming model, serves OpenAI-compatible API
   - **Whisper** (optional, via VoxBox) — Meta's Whisper model, also serves OpenAI-compatible API

4. **Large Language Model (LLM)** — `llama.cpp` (llama-server)
   - Runs local LLMs without external API calls
   - Default: Qwen3-4B-Instruct (4B parameters, suitable for local hardware)
   - Downloads & caches models automatically from Hugging Face
   - Exposes OpenAI-compatible API

5. **Text-to-Speech (TTS)** — `Kokoro`
   - Generates natural voice audio from text
   - Multiple voice options (default: `af_nova`)
   - FastAPI-based service

6. **Frontend** (frontend)
   - Next.js + TypeScript React application
   - Real-time audio I/O via WebRTC
   - Connects to LiveKit signaling server
   - Minimal UI: gets connection details from backend API, displays chat transcript

---

### **Customization Options**

Via .env:

| Variable | Purpose | Example |
|----------|---------|---------|
| `STT_PROVIDER` | Choose STT backend | `nemotron` or `whisper` |
| `STT_BASE_URL` / `STT_MODEL` | Point to custom STT | `http://my-stt:8000/v1`, `custom-model` |
| `LLAMA_HF_REPO` | Swap LLM model | `meta-llama/Llama-2-7b-hf:q4_k_m` |
| `LLAMA_MODEL` | LLM alias used by agent | `my-llm` |
| `LLAMA_BASE_URL` | Custom LLM endpoint | `http://my-llm:8000/v1` |
| `LLAMA_CTX_SIZE` | Context window size | `16384` (larger = more memory) |
| `KOKORO_IMAGE` | TTS image (CPU/GPU) | `ghcr.io/remsky/kokoro-fastapi-gpu:latest` |
| `VOXBOX_HF_REPO_ID` | Whisper model variant | `Systran/faster-whisper-large-v3` |

Code-level customization in agent.py:
- Modify agent system prompt (instructions)
- Add function tools (callable functions the LLM can invoke)
- Change VAD model or turn detection strategy
- Toggle preemptive generation
- Change TTS voice (`voice="af_nova"` → other options)

---

### **Architecture Advantages**

1. **Modularity** — Swap any component (STT/LLM/TTS) without touching others. Run custom STT on one machine, LLM on another.

2. **Real-time Streaming** — WebRTC ensures sub-100ms latency for audio; VAD + preemptive generation = responsive conversations.

3. **Open Standards** — All components expose OpenAI-compatible APIs; can easily swap cloud versions (OpenAI, Groq, AssemblyAI) instead of local.

4. **Privacy & Control** — Everything runs locally; no data leaves your network. No cloud dependencies.

5. **Resource Efficiency** — Containerized; minimal overhead. Can run on CPU or GPU. Multi-GPU support via Docker.

6. **Scalability** — Easy to add monitoring, metrics, rate limiting, or horizontal scaling (multiple LiveKit servers).

---

### **Must It Run in Docker?**

**No, but it's highly recommended:**

- The Docker setup provides isolated, reproducible environments with all dependencies pre-configured
- You *could* set up everything manually:
  - Install Python 3.10+, run LiveKit server binary
  - Install `vox-box`, set up Kokoro, etc.
  - Run `python src/agent.py` in a venv
  - Build Next.js frontend and serve with Node.js
  
But this is tedious and error-prone. Docker abstracts away platform differences (Windows/Mac/Linux) and dependency conflicts.

---

### **Programming Languages & Why**

| Layer | Language | Why |
|-------|----------|-----|
| **Agent Logic** | Python | FastAPI ecosystem, ML/AI libraries, LiveKit Agents SDK officially supports Python; mature for orchestration |
| **Frontend** | TypeScript + React (Next.js) | Modern, type-safe web stack; Next.js provides server-side rendering, API routes, and deployment simplicity |
| **LLM Server** | C++ (`llama.cpp`) | Extreme performance for local inference; memory efficient |
| **STT (Nemotron/Whisper)** | Python | Both models are Python-based; inference optimized via CUDA/tensorrt |
| **TTS (Kokoro)** | Python + FastAPI | Research-friendly framework; easy to wrap in an API |
| **Configuration** | YAML + Shell scripting | Docker Compose is declarative; setup scripts (compose-up.ps1, compose-up.sh) handle multi-platform execution |

---

### **Limitations**

1. **Model Size / Hardware**
   - Qwen3-4B requires ~8-12 GB VRAM or hybrid (CPU + GPU)
   - Larger models (7B+) need 16GB+
   - No adaptive fallback if hardware is insufficient

2. **Latency Variability**
   - First inference is slower (model loading, JIT compilation)
   - Large context sizes slow down LLM generation
   - No dynamic batching across users (single-room design)

3. **Single-Room Architecture**
   - Each voice session is isolated; no multi-user conversation
   - LiveKit supports rooms, but the agent is per-room

4. **Limited Error Recovery**
   - If a service (e.g., Kokoro) crashes, the session may disconnect
   - No automatic retry or fallback; user must reconnect

5. **Tool Calling**
   - Function tools are basic; no complex workflow orchestration
   - No built-in persistent memory or session state beyond current conversation

6. **STT/TTS Accuracy**
   - Local models trade accuracy for speed
   - Whisper is slower than Nemotron but more accurate
   - Kokoro voice quality is good but not as natural as cloud TTS (Google, Apple)

7. **Scaling**
   - Designed for single-server deployment
   - Multi-instance scaling requires external orchestration (Kubernetes, etc.)

8. **Input Method**
   - Voice-only; no text-only fallback UI
   - Requires microphone/speaker hardware

9. **Monitoring & Observability**
   - Minimal logging in Docker Compose setup
   - No built-in metrics collection or alerting

10. **Model Licensing**
    - Some models have specific licenses (e.g., Nemotron research-only)
    - Check compatibility for production use

---

### **Ideal Use Cases**

✅ Local AI assistant for personal use  
✅ Privacy-critical environments (healthcare, legal)  
✅ Custom voice agents for specific tasks  
✅ Development & testing before cloud deployment  
✅ Low-latency real-time interactions  

❌ High-scale multi-user SaaS  
❌ Maximum accuracy required (medical diagnosis)  
❌ Limited compute resources  