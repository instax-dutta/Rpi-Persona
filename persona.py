import os
import sys
import time
import json
import urllib.request
import urllib.error
import psutil

# persona.py - A minimalist, rule-based infrastructure persona for RPi 3.
# Design Intent: Passive monitoring with deterministic logic and optional AI wording.

class PersonaSimulator:
    # Configuration: Adjust these thresholds based on your hardware capabilities.
    # Default values are optimized for Raspberry Pi 3 (1GB RAM).
    THRESHOLDS = {
        "irritated": {"disk": 90, "memory": 90},
        "stressed": {"memory": 80, "cpu": 85},
        "alert": {"cpu": 70, "memory": 65},
        "pleased": {"cpu": 20, "memory": 50, "disk": 70}
        # "calm" is the fallback state
    }

    def __init__(self):
        self.mood = "calm"
        self.energy = 50  # Initial neutral energy
        self.api_key = os.getenv("OLLAMA_API_KEY")
        self.base_messages = {
            "calm": "System operating within tolerances.",
            "alert": "Load is rising. I am paying attention.",
            "stressed": "Resource pressure detected. This is inefficient.",
            "irritated": "Limits exceeded. I do not approve.",
            "pleased": "System health is acceptable. This is preferable."
        }

    @staticmethod
    def format_uptime(seconds):
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")
        
        return " ".join(parts)

    def _get_system_stats(self):
        # Sample resources (CPU call is blocking for 1s to get accurate reading)
        cpu = psutil.cpu_percent(interval=1.0)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        uptime = int(time.time() - psutil.boot_time())
        return {"cpu": cpu, "memory": mem, "disk": disk, "uptime": uptime}

    def _update_state(self, stats):
        # Mood determination (Top-down priority)
        t = self.THRESHOLDS
        
        if stats["disk"] >= t["irritated"]["disk"] or stats["memory"] >= t["irritated"]["memory"]:
            new_mood = "irritated"
        elif stats["memory"] >= t["stressed"]["memory"] or stats["cpu"] >= t["stressed"]["cpu"]:
            new_mood = "stressed"
        elif stats["cpu"] >= t["alert"]["cpu"] or stats["memory"] >= t["alert"]["memory"]:
            new_mood = "alert"
        elif stats["cpu"] <= t["pleased"]["cpu"] and stats["memory"] <= t["pleased"]["memory"] and stats["disk"] <= t["pleased"]["disk"]:
            new_mood = "pleased"
        else:
            new_mood = "calm"

        self.mood = new_mood

        # Energy rules (Apply changes based on mood)
        if self.mood in ["stressed", "irritated"]:
            self.energy -= 5
        elif self.mood == "alert":
            self.energy -= 2
        elif self.mood in ["calm", "pleased"]:
            self.energy += 3
        
        # Clamp energy [0, 100]
        self.energy = max(0, min(100, self.energy))

    def _ai_rephrase(self, message):
        if not self.api_key:
            return message

        payload = {
            "model": "cogito-2.1:671b-cloud",
            "prompt": (
                f"SYSTEM: Preserve meaning exactly. Rephrase only. Max 20 words. "
                f"Tone: Dry, technical, restrained. No emojis. No humor. No roleplay.\n"
                f"USER: {message}"
            ),
            "stream": False,
            "options": { "num_predict": 30, "temperature": 0.1 }
        }

        try:
            req = urllib.request.Request(
                "https://api.ollama.com/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("response", message).strip()
        except Exception:
            return message

    def get_status(self):
        stats = self._get_system_stats()
        self._update_state(stats)
        return {
            "mood": self.mood,
            "energy": self.energy,
            **stats
        }

    def speak(self):
        base_msg = self.base_messages.get(self.mood, self.base_messages["calm"])
        return self._ai_rephrase(base_msg)

# --- DASHBOARD TEMPLATE ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Persona Daemon | {mood}</title>
    <style>
        :root {{
            --bg: #0a0a0a;
            --card-bg: rgba(255, 255, 255, 0.03);
            --border: rgba(255, 255, 255, 0.1);
            --text-main: #f0f0f0;
            --text-dim: #888;
            --accent: {accent};
            --font: 'Inter', -apple-system, blinkmacsystemfont, 'Segoe UI', roboto, sans-serif;
        }}
        * {{ box-sizing: border-box; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }}
        body {{
            background: var(--bg);
            color: var(--text-main);
            font-family: var(--font);
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            overflow: hidden;
        }}
        .container {{ width: 100%; max-width: 480px; padding: 2rem; }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 2rem;
            backdrop-filter: blur(10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        }}
        .header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 2rem; }}
        .mood-label {{ 
            font-size: 0.75rem; font-weight: 800; text-transform: uppercase; 
            letter-spacing: 0.2em; color: var(--accent);
        }}
        .mood-val {{ font-size: 2.5rem; font-weight: 900; margin: 0; filter: drop-shadow(0 0 10px var(--accent)); }}
        .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-top: 2rem; }}
        .stat-item {{ text-align: center; }}
        .stat-val {{ font-size: 1.1rem; font-weight: 700; display: block; }}
        .stat-label {{ font-size: 0.65rem; color: var(--text-dim); text-transform: uppercase; }}
        .message-box {{
            margin-top: 2.5rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--border);
            font-size: 1rem;
            line-height: 1.6;
            color: var(--text-main);
            font-style: italic;
        }}
        .energy-bar-wrap {{
            height: 4px; border-radius: 2px; background: rgba(255,255,255,0.05);
            margin-top: 1rem; overflow: hidden;
        }}
        .energy-bar {{ height: 100%; background: var(--accent); width: {energy}%; }}
        .dot {{ width: 8px; height: 8px; border-radius: 50%; background: var(--accent); display: inline-block; margin-right: 8px; box-shadow: 0 0 10px var(--accent); }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="header">
                <div>
                    <span class="mood-label">System State</span>
                    <h1 class="mood-val">{mood_title}</h1>
                </div>
                <div style="text-align: right">
                    <span style="font-size: 0.7rem; color: var(--text-dim)">Uptime: {uptime}</span>
                </div>
            </div>

            <div class="energy-bar-wrap"><div class="energy-bar"></div></div>
            <div style="font-size: 0.65rem; color: var(--text-dim); margin-top: 0.5rem; letter-spacing: 0.1em">
                ENERGY POTENTIAL: {energy}%
            </div>

            <div class="message-box">
                <span class="dot"></span>"{message}"
            </div>

            <div class="stat-grid">
                <div class="stat-item"><span class="stat-val">{cpu}%</span><span class="stat-label">CPU</span></div>
                <div class="stat-item"><span class="stat-val">{memory}%</span><span class="stat-label">RAM</span></div>
                <div class="stat-item"><span class="stat-val">{disk}%</span><span class="stat-label">DSK</span></div>
            </div>
        </div>
    </div>
    <script>
        setTimeout(() => location.reload(), 5000);
    </script>
</body>
</html>
"""

def run_cli():
    persona = PersonaSimulator()
    status = persona.get_status()
    message = persona.speak()
    print("-" * 30 + f"\\nMOOD:   {status['mood'].upper()}\\nENERGY: {status['energy']}%\\nUPTIME: {persona.format_uptime(status['uptime'])}\\n" + "-" * 30)
    print(f"CPU: {status['cpu']}% | MEM: {status['memory']}% | DISK: {status['disk']}%\\n" + "-" * 30)
    print(f">> {message}\\n" + "-" * 30)

def run_web():
    try:
        from flask import Flask, jsonify
    except ImportError:
        print("Error: Flask required. Run: pip install flask")
        sys.exit(1)

    app = Flask(__name__)
    persona = PersonaSimulator()
    accents = {
        "calm": "#3fb2ff", "alert": "#eccc68", "stressed": "#f97316",
        "irritated": "#ff4757", "pleased": "#2ed573"
    }

    @app.route("/")
    def index():
        status = persona.get_status()
        msg = persona.speak()
        return DASHBOARD_HTML.format(
            mood=status["mood"],
            mood_title=status["mood"].upper(),
            accent=accents.get(status["mood"], accents["calm"]),
            energy=status["energy"],
            message=msg,
            cpu=status["cpu"],
            memory=status["memory"],
            disk=status["disk"],
            uptime=persona.format_uptime(status["uptime"])
        )

    @app.route("/status")
    def status_endpoint():
        s = persona.get_status()
        s["message"] = persona.speak()
        return jsonify(s)

    print("Starting Web Dashboard on port 51987...")
    app.run(host="0.0.0.0", port=51987)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--web":
        run_web()
    else:
        run_cli()
