# RPi Persona Validator

A minimalist, infrastructure-focused persona daemon for Raspberry Pi 3 (ARMv7). It gives your hardware a personality based on system load, expressed through deterministic "moods" and optional AI-rephrased commentary.

## Architecture

- **Single Process**: Designed to run comfortably under 100MB RAM.
- **Deterministic Logic**: System health strictly dictates one of 5 moods (Calm, Alert, Stressed, Irritated, Pleased).
- **Embedded Dashboard**: A sleek, mood-responsive HTML5 dashboard served via Flask (Zero external assets).
- **AI Layer**: Optional integration with Ollama Cloud to rephrase system messages while preserving technical meaning.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/rpi-persona.git
   cd rpi-persona
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### CLI Mode (Default)
Run the script directly to see the monitor output in your terminal.

```bash
python3 persona.py
```

### Web Dashboard Mode
Starts a web server hosting the "Command Center" dashboard at `http://<your-ip>:51987`.

```bash
python3 persona.py --web
```

## Configuration

To enable the AI rephrasing layer, set the `OLLAMA_API_KEY` environment variable.

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Add your key:
   ```bash
   export OLLAMA_API_KEY="your_key_here"
   ```

## Systemd Service (Auto-Start)

1. Edit `persona.service` to match your user/path.
2. Install the service:
   ```bash
   sudo cp persona.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable persona.service
   sudo systemctl start persona.service
   ```

## License

MIT License. See [LICENSE](LICENSE) for details.
