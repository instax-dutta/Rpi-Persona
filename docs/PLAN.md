# PLAN: RPi Persona Simulator - Open Source Prep

## 1. Project Overview
A minimalist, rule-based infrastructure daemon with a personality, designed for Raspberry Pi 3. It monitors system resources and reflects a "persona" state (mood and energy) based on deterministic rules.

## 2. Architecture
- **Language**: Python 3.
- **Dependencies**: `psutil` (required), `Flask` (optional for web mode), `requests`/`urllib` (for Ollama).
- **Structure**: Single file `persona.py`.
- **Runtime**: Single process, synchronous.

## 3. Components
### A. System Monitor
- Sample CPU, Memory, Disk, and Uptime.

### B. Persona Engine
- **State**: `mood` and `energy`.
- **Logic**: Deterministic rule chain with energy mutations.

### C. Communication Layer
- **Static Messages**: Base sentences.
- **AI Rephrasing**: Optional Ollama Cloud integration (`cogito-2.1:671b-cloud`).

### D. Web UI
- **Dashboard**: A minimalist, high-end HTML/CSS interface.
- **Styling**: Vanilla CSS, Dark Mode, Glassmorphism.

## 4. Open Source Cleanup (Current Phase)
### A. Security Scrub
- **Action**: REMOVE hardcoded API key from `persona.py`.
- **Action**: Verify no other secrets exist in history (if using git, but here we just ensure the file is clean).

### B. Configuration
- **Environment**: Shift to `.env` file support or strictly environment variables.
- **Example**: Create `.env.example`.

### C. Documentation
- **README.md**: Add installation, usage (CLI/Web), and configuration guide.
- **requirements.txt**: explicit dependency list.
- **LICENSE**: Add MIT License.
- **.gitignore**: Ignore `__pycache__`, `.env`, etc.

## 5. Implementation Steps
1. **Sanitize**: Edit `persona.py` to revert to `os.getenv`.
2. **Docs**: Create `README.md`, `LICENSE`, `requirements.txt`.
3. **Config**: Create `.env.example`.
4. **.gitignore**: Create `.gitignore`.

## 6. Verification
- **Security Scan**: Run `security_scan.py` to confirm no secrets.
- **Functionality**: Verify invalid config handles gracefully.
