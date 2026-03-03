<div align="center">
  <img src="banner.png?v=3" alt="Rpi Persona Banner" width="100%" />
  
# RPi Persona Daemon
  
  <a href="https://github.com/instax-dutta/Rpi-Persona">
    <img src="https://img.shields.io/badge/GitHub-Repo-181717?logo=github" alt="Github Repo" />
  </a>
  <img src="https://img.shields.io/badge/Python-3.x-blue?logo=python" alt="Python Version" />
  <img src="https://img.shields.io/badge/Lightweight-Yes-green" alt="Lightweight" />

  **Infrastructure with a Personality.**  
  *A minimalist, aesthetic daemon that gives your server a voice based on its health.*
</div>

---

## 🧪 Tested on the below machine

**Hardware Specs:**

- **Device**: Raspberry Pi 3 Model B (v1.2)
- **CPU**: Quad Core 1.2GHz Broadcom BCM2837 64bit
- **RAM**: 1GB LPDDR2 (900MHz)
- **Status**: Running `persona.py` with **< 2% CPU** and **~15MB RAM** usage.

---

## 🚀 Overview

**RPi Persona** is a rule-based monitoring daemon that monitors system resources and expresses a "Mood" and "Energy" state.

While originally **optimized for the Raspberry Pi 3 (1GB RAM)**, it scales beautifully across VPS instances and local development machines, providing a premium, "living" dashboard for your infrastructure.

### ✨ Features

- **Ultra-Lightweight**: Single-file Python script (~670 lines). Extremely low resource footprint.
- **Zero External JS**: No animation libraries - pure CSS-only animations.
- **Hardware Awareness**: Tracks **CPU Temperature**, **Network Latency**, and **Dominant Processes**.
- **Temporal Memory**: 60-second rolling buffer for **Trend Analysis** and **Volatility Tracking**.
- **Efficient Updates**: 3-second SSE interval - optimized for human perception.
- **Technical Aesthetic**: "Instrument" design language - monospace precision, subtle textures.
- **AI-Ready**: Optional integration with **Ollama Cloud** to rephrase dry stats into personality-driven commentary.
- **Optimized Backend**: Multi-layer caching reduces system calls by ~95%.

---

## 📦 Installation

This daemon is designed to be "drop-in" ready.

1. **Clone the repository**

   ```bash
   git clone https://github.com/instax-dutta/Rpi-Persona.git
   cd Rpi-Persona
   ```

2. **Install minimal dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   *(Only `psutil` and `flask` are required)*

---

## 🛠️ Usage

### 1. CLI Mode (Headless)

Ideal for SSH sessions or remote health checks.

```bash
python3 persona.py
```

*Output:*

```text
------------------------------
MOOD:   CALM
ENERGY: 53%
UPTIME: 1d 8h 3m 50s
------------------------------
CPU:    1.2% | MEM: 14.5% | DISK: 8.5%
------------------------------
>> System operating within tolerances.
------------------------------
```

### 2. Web Dashboard (Command Center)

Starts a sleek, real-time dashboard at `http://localhost:51987`.

```bash
python3 persona.py --web
```

---

## ⚡ Performance Optimizations

### Backend (Python)

| Operation | Before | After |
|-----------|--------|-------|
| Network Latency | Socket created every call | Cached 30s |
| Top Process | Unreliable modulo check | Timestamp-based 5s cache |
| AI Rephrase | Called every update | Cached 30s + mood-change trigger |
| History Average | O(n) sum each call | O(1) running sum |
| System Stats | Always re-read | Cached 1s, reused across SSE |

### Frontend (HTML/CSS/JS)

| Aspect | Before | After |
|--------|--------|-------|
| External JS | ~85KB (GSAP) | **Zero** |
| Update Interval | 1 second | 3 seconds |
| Animations | JavaScript-driven | CSS-only (`@keyframes`) |
| Heavy Effects | 100px blur filter | CSS gradient only |
| DOM Updates | Per-element gsap calls | Single batch update |

### Design Philosophy

The frontend follows a **"Technical Instrument"** aesthetic:

- **Typography**: JetBrains Mono (data) + Instrument Sans (labels)
- **Visual**: Subtle noise texture, precise borders, minimal glow
- **Motion**: GPU-accelerated CSS transitions, native pulse animation
- **Efficiency**: Every pixel serves a purpose

```python
CACHE_TTL = {
    "latency": 30,      # Network changes slowly
    "top_proc": 5,      # Process changes infrequently  
    "ai_message": 30   # Only rephrase on mood change or TTL
}
```

- **Thread-Safe**: Uses `threading.RLock()` for concurrent access in Flask's threaded mode.
- **Graceful Degradation**: Falls back to cached values if sensors/network fail.
- **Batched I/O**: Memory and disk stats fetched in single psutil call.

---

## 🤖 AI Integration (Ollama)

By default, the daemon uses hardcoded "Base Messages". You can give it a brain by connecting it to an LLM via **Ollama Cloud**.

1. **Get an API Key** from your Ollama provider.
2. **Set the Environment Variable**:

   ```bash
   export OLLAMA_API_KEY="your_key_here"
   ```

3. **Run**: The daemon will automatically detect the key and rephrase its status messages dynamically while maintaining its "Dry, Technical, Restrained" tone.

---

## ⚙️ Customization (Fine-Tuning)

You can fine-tune the thresholds for moods (including thermal limits) by editing the `THRESHOLDS` dictionary:

```python
THRESHOLDS = {
    "irritated": {"disk": 90, "memory": 90, "temp": 80},
    "stressed":  {"memory": 80, "cpu": 85, "temp": 70},
    "alert":     {"cpu": 70, "memory": 65, "temp": 60},
    ...
}
```

You can also adjust cache TTL values in `CACHE_TTL` to balance responsiveness vs. resource usage.

---

## 🧩 Architecture

- **Reactive Core**: Uses **SSE** for efficient updates without WebSocket overhead.
- **Lightweight Frontend**: Zero external JS libraries, CSS-only animations, batch DOM updates.
- **Hardware Sensors**: Direct reads from `/sys/class/thermal` for near-zero CPU temperature overhead.
- **Trend Memory**: Implemented via `collections.deque` with O(1) average calculation.
- **Cache Layer**: Centralized timestamp-based TTL caching for all expensive operations.
- **Thread-Safe**: Proper locking for concurrent Flask requests.

---

## 📄 License

MIT License. Open source and free to use, modify, and host.
