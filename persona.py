import os
import sys
import time
import json
import urllib.request
import urllib.error
import psutil
import socket
from collections import deque

# persona.py - A minimalist, rule-based infrastructure persona for RPi 3.
# Design Intent: Passive monitoring with deterministic logic and optional AI wording.

class PersonaSimulator:
    # Configuration: Adjust these thresholds based on your hardware capabilities.
    # Default values are optimized for Raspberry Pi 3 (1GB RAM).
    THRESHOLDS = {
        "irritated": {"disk": 90, "memory": 90, "temp": 80},
        "stressed": {"memory": 80, "cpu": 85, "temp": 70},
        "alert": {"cpu": 70, "memory": 65, "temp": 60},
        "pleased": {"cpu": 20, "memory": 50, "disk": 70, "temp": 50}
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
        self.history = deque(maxlen=60)  # 60s of temporal memory
        self._top_proc_cache = "N/A"

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
                return float(f.read()) / 1000.0
        except:
            return 0.0  # Fallback for non-Pi

    def _get_latency(self):
        try:
            start = time.time()
            socket.create_connection(("8.8.8.8", 53), timeout=1).close()
            return int((time.time() - start) * 1000)
        except:
            return 999

    def _get_top_proc(self):
        try:
            # Only update every few seconds to save CPU
            if int(time.time()) % 5 == 0:
                procs = sorted(psutil.process_iter(['name', 'cpu_percent']), key=lambda p: p.info['cpu_percent'], reverse=True)
                self._top_proc_cache = procs[0].info['name'] if procs else "N/A"
            return self._top_proc_cache
        except:
            return "N/A"

    def _get_system_stats(self):
        cpu = psutil.cpu_percent(interval=None) # Interval None for non-blocking
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        temp = self._get_cpu_temp()
        latency = self._get_latency()
        top_proc = self._get_top_proc()
        uptime = int(time.time() - psutil.boot_time())
        return {
            "cpu": cpu, "memory": mem, "disk": disk, 
            "temp": temp, "latency": latency, "uptime": uptime,
            "top_proc": top_proc
        }

    def _update_state(self, stats):
        self.history.append(stats["cpu"])
        avg_cpu = sum(self.history) / len(self.history)
        volatility = max(self.history) - min(self.history) if len(self.history) > 1 else 0

        t = self.THRESHOLDS
        # Priority: Temp > Disk/Mem > CPU
        if stats["temp"] >= t["irritated"]["temp"] or stats["disk"] >= t["irritated"]["disk"] or stats["memory"] >= t["irritated"]["memory"]:
            new_mood = "irritated"
        elif stats["temp"] >= t["stressed"]["temp"] or stats["memory"] >= t["stressed"]["memory"] or stats["cpu"] >= t["stressed"]["cpu"]:
            new_mood = "stressed"
        elif stats["temp"] >= t["alert"]["temp"] or stats["cpu"] >= t["alert"]["cpu"] or stats["memory"] >= t["alert"]["memory"]:
            new_mood = "alert"
        elif stats["cpu"] <= t["pleased"]["cpu"] and stats["temp"] <= t["pleased"]["temp"]:
            new_mood = "pleased"
        else:
            new_mood = "calm"
        
        # If volatility is high, push mood towards alert
        if volatility > 50 and new_mood == "calm":
            new_mood = "alert"

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
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
    <style>
        :root {{
            --bg: #050505;
            --card-bg: rgba(255, 255, 255, 0.02);
            --border: rgba(255, 255, 255, 0.08);
            --text-main: #ffffff;
            --text-dim: #777;
            --accent: {accent};
            --font: 'Outfit', 'Inter', system-ui, sans-serif;
        }}
        * {{ box-sizing: border-box; transition: color 0.4s, background 0.4s; }}
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
        .orb {{
            position: absolute;
            width: 600px; height: 600px;
            background: radial-gradient(circle, var(--accent) 0%, transparent 70%);
            opacity: 0.15;
            filter: blur(100px);
            z-index: -1;
            transition: all 2s ease;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 32px;
            padding: 2.5rem;
            backdrop-filter: blur(40px);
            box-shadow: 0 40px 100px rgba(0,0,0,0.8);
            width: 100%;
            max-width: 440px;
            position: relative;
            overflow: hidden;
        }}
        .header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 2rem; }}
        .mood-label {{ 
            font-size: 0.7rem; font-weight: 700; text-transform: uppercase; 
            letter-spacing: 0.3em; color: var(--accent); opacity: 0.8;
        }}
        .mood-val {{ font-size: 3rem; font-weight: 900; margin: 0; letter-spacing: -0.02em; }}
        .uptime {{ font-size: 0.7rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.1em; }}
        
        .energy-wrap {{ margin: 2rem 0; }}
        .energy-bar-bg {{ height: 4px; border-radius: 2px; background: rgba(255,255,255,0.05); overflow: hidden; }}
        .energy-bar {{ height: 100%; background: var(--accent); width: {energy}%; box-shadow: 0 0 20px var(--accent); }}
        
        .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-top: 2rem; }}
        .stat-item {{ padding: 1rem; background: rgba(255,255,255,0.02); border-radius: 16px; border: 1px solid var(--border); }}
        .stat-val {{ font-size: 1.25rem; font-weight: 700; display: block; }}
        .stat-label {{ font-size: 0.6rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.1em; }}
        
        .message-box {{
            margin-top: 2rem;
            font-size: 1.1rem;
            line-height: 1.5;
            color: #ddd;
            font-style: italic;
            min-height: 3.3em;
        }}
        .top-proc {{ 
            margin-top: 1rem; font-size: 0.65rem; color: var(--text-dim); 
            border-left: 2px solid var(--accent); padding-left: 0.5rem;
        }}
        
        .pulse {{ width: 12px; height: 12px; border-radius: 50%; background: var(--accent); display: inline-block; margin-right: 12px; }}
    </style>
</head>
<body>
    <div class="orb" id="orb"></div>
    <div class="card">
        <div class="header">
            <div>
                <span class="mood-label" id="status-label">System State</span>
                <h1 class="mood-val" id="mood-title">{mood_title}</h1>
            </div>
            <div style="text-align: right">
                <span class="uptime" id="uptime-val">Uptime: {uptime}</span>
            </div>
        </div>

        <div class="energy-wrap">
            <div class="energy-bar-bg"><div class="energy-bar" id="energy-bar" style="width: {energy}%"></div></div>
            <div style="font-size: 0.6rem; color: var(--text-dim); margin-top: 0.75rem; letter-spacing: 0.1em">
                POTENTIAL: <span id="energy-val">{energy}</span>%
            </div>
        </div>

        <div class="message-box" id="message">
            "{message}"
        </div>
        
        <div class="top-proc">Dominant Process: <span id="top-proc" style="color: #fff">{top_proc}</span></div>

        <div class="stat-grid">
            <div class="stat-item"><span class="stat-val" id="cpu-val">{cpu}%</span><span class="stat-label">CPU LOAD</span></div>
            <div class="stat-item"><span class="stat-val" id="temp-val">{temp}°C</span><span class="stat-label">CORE TEMP</span></div>
            <div class="stat-item"><span class="stat-val" id="mem-val">{memory}%</span><span class="stat-label">MEMORY</span></div>
            <div class="stat-item"><span class="stat-val" id="lat-val">{latency}ms</span><span class="stat-label">LATENCY</span></div>
        </div>
    </div>

    <script>
        const accents = {{
            "calm": "#3fb2ff", "alert": "#eccc68", "stressed": "#f97316",
            "irritated": "#ff4757", "pleased": "#2ed573"
        }};

        function updateUI(data) {{
            const accent = accents[data.mood] || accents.calm;
            document.documentElement.style.setProperty('--accent', accent);
            
            gsap.to("#mood-title", {{ duration: 0.5, textContent: data.mood.toUpperCase() }});
            document.getElementById("message").textContent = `"${{data.message}}"`;
            document.getElementById("uptime-val").textContent = `Uptime: ${{data.uptime_formatted}}`;
            
            gsap.to("#energy-bar", {{ width: `${{data.energy}}%`, duration: 1, ease: "power2.out" }});
            document.getElementById("energy-val").textContent = data.energy;
            
            document.getElementById("cpu-val").textContent = `${{data.cpu}}%`;
            document.getElementById("temp-val").textContent = `${{data.temp}}°C`;
            document.getElementById("mem-val").textContent = `${{data.memory}}%`;
            document.getElementById("lat-val").textContent = `${{data.latency}}ms`;
            document.getElementById("top-proc").textContent = data.top_proc;

            gsap.to("#orb", {{ background: `radial-gradient(circle, ${{accent}} 0%, transparent 70%)`, duration: 2 }});
        }}

        const evtSource = new EventSource("/events");
        evtSource.onmessage = function(event) {{
            const data = JSON.parse(event.data);
            updateUI(data);
        }};

        // Heartbeat animation
        gsap.to(".card", {{ scale: 1.01, duration: 2, repeat: -1, yoyo: true, ease: "sine.inOut" }});
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
        from flask import Flask, jsonify, Response, stream_with_context
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
                time.sleep(1)
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
