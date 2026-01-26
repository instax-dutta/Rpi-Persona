<div align="center">
  <img src="https://media.discordapp.net/attachments/1089947938917871636/1199321796120232016/banner.png" alt="Rpi Persona Banner" width="100%" /> 
  
  # RPi Persona Daemon
  
  <a href="https://github.com/instax-dutta/Rpi-Persona">
    <img src="https://img.shields.io/badge/GitHub-Repo-181717?logo=github" alt="Github Repo" />
  </a>
  <img src="https://img.shields.io/badge/Python-3.x-blue?logo=python" alt="Python Version" />
  <img src="https://img.shields.io/badge/Lightweight-Yes-green" alt="Lightweight" />
  <img src="https://img.shields.io/badge/Platform-Any-orange" alt="Platform Agnostic" />

  **Infrastructure with a Personality.**  
  *A minimalist, aesthetic daemon that gives your server a voice based on its health.*
</div>

---

## 🚀 Overview

**RPi Persona** is a rule-based monitoring daemon that monitors system resources (CPU, RAM, Disk) and expresses a "Mood" and "Energy" state. 

While originally **optimized for the Raspberry Pi 3 (1GB RAM)** to run under <100MB memory, the code is platform-agnostic. It runs beautifully on high-end servers, VPS instances, or local Windows/Mac development machines.

### ✨ Features
- **Ultra-Lightweight**: Single-file Python script. No heavy dependencies.
- **Deterministic Persona**: Moods (Calm, Alert, Stressed, Irritated, Pleased) are derived directly from system load rules.
- **Premium Dashboard**: Embedded HTML5/CSS Glassmorphism dashboard (Zero external requests).
- **AI-Ready**: Optional integration with **Ollama Cloud** to rephrase the dry technical status into sardonic, personality-driven commentary.

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
Ideal for SSH sessions or logs.

```bash
python3 persona.py
```
*Output:*
```text
------------------------------
MOOD:   CALM
ENERGY: 53%
------------------------------
CPU:    1.2%
MEM:    14.5%
DISK:   8.5%
UPTIME: 3128s
------------------------------
>> System operating within tolerances.
------------------------------
```

### 2. Web Dashboard (Command Center)
Starts a sleek, dark-mode dashboard at `http://localhost:51987`.

```bash
python3 persona.py --web
```

---

## 🤖 AI Integration (Ollama)

By default, the daemon uses hardcoded "Base Messages". You can give it a brain by connecting it to an LLM via **Ollama Cloud** (or local Ollama).

1. **Get an API Key** from your Ollama provider.
2. **Set the Environment Variable**:
   ```bash
   export OLLAMA_API_KEY="your_key_here"
   ```
3. **Run**: The daemon will now detect the key and rephrase its status messages dynamically while maintaining its "Dry, Technical, Restrained" tone.

> **For Developers:** The prompt logic is located in the `_ai_rephrase` method. Feel free to tweak the prompt to change the persona (e.g., make it "Pirate Mode" or "Cyberpunk").

---

## ⚙️ Customization (Fine-Tuning)

We know 80% RAM usage on a Raspberry Pi is different from 80% on a 64GB Workstation. 

You can fine-tune the strictness of the persona by editing the `THRESHOLDS` dictionary at the top of `persona.py`:

```python
class PersonaSimulator:
    # Adjust these based on your machine's muscle
    THRESHOLDS = {
        "irritated": {"disk": 90, "memory": 90},
        "stressed": {"memory": 80, "cpu": 85}, # Raise this for powerful PCs
        ...
    }
```

---

## 🧩 Architecture

- **Single File**: `persona.py` contains the Logic, API Client, and HTML Template.
- **No Vectors/Embeddings**: Logic is pure Python `if/else` for reliability.
- **Synchronous**: Uses `psutil` blocking calls for accurate instant sampling without thread overhead.

## 📄 License

MIT License. Open source and free to use, modify, and host.
