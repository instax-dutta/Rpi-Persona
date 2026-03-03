import os
import sys
import time
import json
import threading
import urllib.request
import urllib.error
import psutil
import socket
from collections import deque

# persona.py - A minimalist, rule-based infrastructure persona for RPi 3.
# Optimized: Caching, thread-safety, graceful degradation, lightweight frontend.

class PersonaSimulator:
    THRESHOLDS = {
        "irritated": {"disk": 90, "memory": 90, "temp": 80},
        "stressed": {"memory": 80, "cpu": 85, "temp": 70},
        "alert": {"cpu": 70, "memory": 65, "temp": 60},
        "pleased": {"cpu": 20, "memory": 50, "disk": 70, "temp": 50}
    }

    CACHE_TTL = {
        "latency": 30,
        "top_proc": 5,
        "ai_message": 30
    }

    def __init__(self):
        self._lock = threading.RLock()
        self.mood = "calm"
        self.energy = 50
        self.api_key = os.getenv("OLLAMA_API_KEY")
        self.base_messages = {
            "calm": "System operating within tolerances.",
            "alert": "Load is rising. I am paying attention.",
            "stressed": "Resource pressure detected. This is inefficient.",
            "irritated": "Limits exceeded. I do not approve.",
            "pleased": "System health is acceptable. This is preferable."
        }
        
        self.history = deque(maxlen=60)
        self._history_sum = 0.0
        
        self._cache = {
            "latency": {"value": 999, "timestamp": 0},
            "top_proc": {"value": "N/A", "timestamp": 0},
            "system_stats": {"value": None, "timestamp": 0},
            "ai_message": {"value": None, "timestamp": 0, "mood": None}
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

    def _get_cpu_temp(self):
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                return float(f.read().strip()) / 1000.0
        except (IOError, OSError, ValueError):
            return self._cache.get("system_stats", {}).get("value", {}).get("temp", 0.0) if self._cache["system_stats"]["value"] else 0.0

    def _get_latency(self):
        now = time.time()
        cached = self._cache["latency"]
        
        if now - cached["timestamp"] < self.CACHE_TTL["latency"]:
            return cached["value"]
        
        try:
            start = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)
            sock.connect(("8.8.8.8", 53))
            sock.close()
            latency = int((time.time() - start) * 1000)
        except (socket.error, OSError):
            latency = cached["value"] if cached["value"] != 999 else 999
        
        cached["value"] = latency
        cached["timestamp"] = now
        return latency

    def _get_top_proc(self):
        now = time.time()
        cached = self._cache["top_proc"]
        
        if now - cached["timestamp"] < self.CACHE_TTL["top_proc"]:
            return cached["value"]
        
        try:
            procs = []
            for p in psutil.process_iter(['name', 'cpu_percent']):
                try:
                    procs.append(p)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if procs:
                valid_procs = [p for p in procs[:20] if p.info.get('cpu_percent') is not None]
                if valid_procs:
                    top_proc = max(valid_procs, key=lambda p: p.info.get('cpu_percent') or 0)
                    name = top_proc.info.get('name', 'N/A')
                else:
                    name = "N/A"
            else:
                name = "N/A"
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            name = cached["value"] if cached["value"] != "N/A" else "N/A"
        
        cached["value"] = name
        cached["timestamp"] = now
        return name

    def _get_system_stats(self):
        now = time.time()
        cached = self._cache["system_stats"]
        
        if cached["value"] and (now - cached["timestamp"]) < 1.0:
            return cached["value"]
        
        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            stats = {
                "cpu": cpu, 
                "memory": mem.percent, 
                "disk": disk.percent, 
                "temp": self._get_cpu_temp(),
                "latency": self._get_latency(),
                "top_proc": self._get_top_proc(),
                "uptime": int(time.time() - psutil.boot_time())
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            stats = cached["value"] if cached["value"] else {}
        
        cached["value"] = stats
        cached["timestamp"] = now
        return stats

    def _update_state(self, stats):
        cpu = stats.get("cpu", 0)
        
        if len(self.history) == self.history.maxlen:
            self._history_sum -= self.history[0]
        
        self.history.append(cpu)
        self._history_sum += cpu
        
        avg_cpu = self._history_sum / len(self.history) if self.history else 0
        volatility = max(self.history) - min(self.history) if len(self.history) > 1 else 0

        t = self.THRESHOLDS
        temp = stats.get("temp", 0)
        memory = stats.get("memory", 0)
        disk = stats.get("disk", 0)
        
        if temp >= t["irritated"]["temp"] or disk >= t["irritated"]["disk"] or memory >= t["irritated"]["memory"]:
            new_mood = "irritated"
        elif temp >= t["stressed"]["temp"] or memory >= t["stressed"]["memory"] or cpu >= t["stressed"]["cpu"]:
            new_mood = "stressed"
        elif temp >= t["alert"]["temp"] or cpu >= t["alert"]["cpu"] or memory >= t["alert"]["memory"]:
            new_mood = "alert"
        elif cpu <= t["pleased"]["cpu"] and temp <= t["pleased"]["temp"]:
            new_mood = "pleased"
        else:
            new_mood = "calm"
        
        if volatility > 50 and new_mood == "calm":
            new_mood = "alert"

        self.mood = new_mood

        if self.mood in ["stressed", "irritated"]:
            self.energy -= 5
        elif self.mood == "alert":
            self.energy -= 2
        elif self.mood in ["calm", "pleased"]:
            self.energy += 3
        
        self.energy = max(0, min(100, self.energy))

    def _ai_rephrase(self, message):
        if not self.api_key:
            return message

        now = time.time()
        cached = self._cache["ai_message"]
        
        if (cached["mood"] == self.mood and 
            now - cached["timestamp"] < self.CACHE_TTL["ai_message"] and 
            cached["value"]):
            return cached["value"]

        payload = {
            "model": "cogito-2.1:671b-cloud",
            "prompt": (
                f"SYSTEM: Preserve meaning exactly. Rephrase only. Max 20 words. "
                f"Tone: Dry, technical, restrained. No emojis. No humor. No roleplay.\n"
                f"USER: {message}"
            ),
            "stream": False,
            "options": {"num_predict": 30, "temperature": 0.1}
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
                rephrased = result.get("response", message).strip()
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError):
            rephrased = message
        
        cached["value"] = rephrased
        cached["mood"] = self.mood
        cached["timestamp"] = now
        return rephrased

    def get_status(self):
        with self._lock:
            stats = self._get_system_stats()
            self._update_state(stats)
            return {
                "mood": self.mood,
                "energy": self.energy,
                **stats
            }

    def speak(self):
        with self._lock:
            base_msg = self.base_messages.get(self.mood, self.base_messages["calm"])
            return self._ai_rephrase(base_msg)

# --- OPTIMIZED DASHBOARD TEMPLATE ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Persona | {mood}</title>
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Instrument+Sans:wght@400;600;700&display=swap');
        
        :root {{
            --bg: #0a0a0a;
            --surface: rgba(255,255,255,0.025);
            --border: rgba(255,255,255,0.06);
            --text: #e8e8e8;
            --text-dim: #555;
            --accent: {accent};
            --accent-dim: {accent}40;
            --mono: 'JetBrains Mono', monospace;
            --sans: 'Instrument Sans', system-ui, sans-serif;
        }}
        
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
        
        body {{
            background: var(--bg);
            color: var(--text);
            font-family: var(--sans);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }}
        
        body::before {{
            content: '';
            position: fixed;
            inset: 0;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
            opacity: 0.015;
            pointer-events: none;
            z-index: 0;
        }}
        
        .container {{
            position: relative;
            z-index: 1;
            width: 100%;
            max-width: 380px;
            padding: 2rem;
        }}
        
        .gauge {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 2rem;
            position: relative;
            overflow: hidden;
        }}
        
        .gauge::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: var(--accent);
            opacity: 0.8;
        }}
        
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1.5rem;
        }}
        
        .mood-block {{}}
        
        .mood-label {{
            font-family: var(--mono);
            font-size: 0.6rem;
            text-transform: uppercase;
            letter-spacing: 0.2em;
            color: var(--accent);
            margin-bottom: 0.25rem;
        }}
        
        .mood-value {{
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            line-height: 1;
            transition: color 0.5s ease;
        }}
        
        .uptime {{
            font-family: var(--mono);
            font-size: 0.65rem;
            color: var(--text-dim);
            text-align: right;
        }}
        
        .energy-section {{
            margin: 1.5rem 0;
        }}
        
        .energy-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        }}
        
        .energy-label {{
            font-family: var(--mono);
            font-size: 0.55rem;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            color: var(--text-dim);
        }}
        
        .energy-value {{
            font-family: var(--mono);
            font-size: 0.65rem;
            color: var(--accent);
        }}
        
        .energy-track {{
            height: 3px;
            background: var(--border);
            border-radius: 2px;
            overflow: hidden;
        }}
        
        .energy-fill {{
            height: 100%;
            background: var(--accent);
            width: {energy}%;
            transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
        }}
        
        .energy-fill::after {{
            content: '';
            position: absolute;
            right: 0;
            top: 0;
            bottom: 0;
            width: 8px;
            background: inherit;
            filter: blur(4px);
            opacity: 0.6;
            animation: pulse 2s ease-in-out infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 0.6; transform: scaleX(1); }}
            50% {{ opacity: 1; transform: scaleX(1.2); }}
        }}
        
        .message {{
            margin: 1.5rem 0;
            padding: 1rem;
            background: rgba(255,255,255,0.015);
            border-left: 2px solid var(--accent-dim);
            border-radius: 0 8px 8px 0;
            font-size: 0.85rem;
            line-height: 1.6;
            color: #bbb;
            font-style: italic;
            min-height: 4rem;
            display: flex;
            align-items: center;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
            margin-top: 1.5rem;
        }}
        
        .stat {{
            background: rgba(255,255,255,0.02);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 0.85rem;
            transition: border-color 0.3s ease;
        }}
        
        .stat-value {{
            font-family: var(--mono);
            font-size: 1.1rem;
            font-weight: 600;
            display: block;
            margin-bottom: 0.2rem;
        }}
        
        .stat-label {{
            font-family: var(--mono);
            font-size: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            color: var(--text-dim);
        }}
        
        .proc {{
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
            font-family: var(--mono);
            font-size: 0.6rem;
            color: var(--text-dim);
            display: flex;
            gap: 0.5rem;
        }}
        
        .proc-label {{ color: var(--text-dim); }}
        .proc-value {{ color: var(--text); }}
        
        .status-dot {{
            display: inline-block;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--accent);
            margin-right: 0.5rem;
            animation: blink 3s ease-in-out infinite;
        }}
        
        @keyframes blink {{
            0%, 90%, 100% {{ opacity: 1; }}
            95% {{ opacity: 0.3; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="gauge">
            <div class="header">
                <div class="mood-block">
                    <div class="mood-label"><span class="status-dot"></span>State</div>
                    <div class="mood-value" id="mood">{mood_title}</div>
                </div>
                <div class="uptime" id="uptime">{uptime}</div>
            </div>
            
            <div class="energy-section">
                <div class="energy-header">
                    <span class="energy-label">Potential</span>
                    <span class="energy-value" id="energy">{energy}%</span>
                </div>
                <div class="energy-track">
                    <div class="energy-fill" id="energy-bar" style="width: {energy}%"></div>
                </div>
            </div>
            
            <div class="message" id="message">
                "{message}"
            </div>
            
            <div class="stats-grid">
                <div class="stat">
                    <span class="stat-value" id="cpu">{cpu}%</span>
                    <span class="stat-label">CPU</span>
                </div>
                <div class="stat">
                    <span class="stat-value" id="temp">{temp}°</span>
                    <span class="stat-label">Temp</span>
                </div>
                <div class="stat">
                    <span class="stat-value" id="mem">{memory}%</span>
                    <span class="stat-label">RAM</span>
                </div>
                <div class="stat">
                    <span class="stat-value" id="lat">{latency}ms</span>
                    <span class="stat-label">Net</span>
                </div>
            </div>
            
            <div class="proc">
                <span class="proc-label">TOP:</span>
                <span class="proc-value" id="proc">{top_proc}</span>
            </div>
        </div>
    </div>

    <script>
        const accents = {{
            "calm": "#4a9eff",
            "alert": "#f0c040",
            "stressed": "#ff8840",
            "irritated": "#ff4050",
            "pleased": "#40d080"
        }};

        const el = {{
            mood: document.getElementById('mood'),
            uptime: document.getElementById('uptime'),
            energy: document.getElementById('energy'),
            energyBar: document.getElementById('energy-bar'),
            message: document.getElementById('message'),
            cpu: document.getElementById('cpu'),
            temp: document.getElementById('temp'),
            mem: document.getElementById('mem'),
            lat: document.getElementById('lat'),
            proc: document.getElementById('proc'),
            root: document.documentElement
        }};

        function update(data) {{
            const accent = accents[data.mood] || accents.calm;
            el.root.style.setProperty('--accent', accent);
            el.mood.textContent = data.mood.toUpperCase();
            el.uptime.textContent = data.uptime_formatted;
            el.energy.textContent = data.energy + '%';
            el.energyBar.style.width = data.energy + '%';
            el.message.textContent = '"' + data.message + '"';
            el.cpu.textContent = data.cpu + '%';
            el.temp.textContent = data.temp + '°';
            el.mem.textContent = data.memory + '%';
            el.lat.textContent = data.latency + 'ms';
            el.proc.textContent = data.top_proc;
        }}

        const evt = new EventSource("/events");
        evt.onmessage = e => update(JSON.parse(e.data));
    </script>
</body>
</html>
"""

def run_cli():
    persona = PersonaSimulator()
    status = persona.get_status()
    message = persona.speak()
    print("-" * 30 + f"\nMOOD:   {status['mood'].upper()}\nENERGY: {status['energy']}%\nUPTIME: {persona.format_uptime(status['uptime'])}\n" + "-" * 30)
    print(f"CPU: {status['cpu']}% | MEM: {status['memory']}% | DISK: {status['disk']}%\n" + "-" * 30)
    print(f">> {message}\n" + "-" * 30)

def run_web():
    try:
        from flask import Flask, jsonify, Response, stream_with_context, send_from_directory
    except ImportError:
        print("Error: Flask required. Run: pip install flask")
        sys.exit(1)

    app = Flask(__name__)
    persona = PersonaSimulator()
    accents = {
        "calm": "#4a9eff", "alert": "#f0c040", "stressed": "#ff8840",
        "irritated": "#ff4050", "pleased": "#40d080"
    }

    @app.route("/favicon.svg")
    def favicon():
        from flask import send_file
        try:
            return send_file("favicon.svg", mimetype="image/svg+xml")
        except:
            return "", 404

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
            temp=status["temp"],
            latency=status["latency"],
            top_proc=status["top_proc"],
            uptime=persona.format_uptime(status["uptime"])
        )

    @app.route("/events")
    def events():
        def generate():
            while True:
                status = persona.get_status()
                status["message"] = persona.speak()
                status["uptime_formatted"] = persona.format_uptime(status["uptime"])
                yield f"data: {json.dumps(status)}\n\n"
                time.sleep(3)
        return Response(stream_with_context(generate()), mimetype="text/event-stream")

    @app.route("/status")
    def status_endpoint():
        s = persona.get_status()
        s["message"] = persona.speak()
        return jsonify(s)

    print("Starting Web Dashboard on port 51987...")
    app.run(host="0.0.0.0", port=51987, threaded=True)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--web":
        run_web()
    else:
        run_cli()
