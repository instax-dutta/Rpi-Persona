# PLAN: RPi Persona Evolution (Lightweight)

## Objective
Implement three major enhancements (Environmental Awareness, Kinetic UI, and Temporal Memory) to the RPi Persona daemon while maintaining its minimalist footprint on Raspberry Pi 3.

## Phase 1: Planning & Infrastructure
- [ ] Define data structures for historical stat tracking (Temporal Memory).
- [ ] Identify low-level methods for temperature and process monitoring (Environmental Awareness).
- [ ] Design the SSE endpoint and frontend listener logic (Reactive Bridge).

## Phase 2: Backend Implementation (PersonaSimulator updates)
- [ ] **Environmental Awareness**:
    - Add `_get_cpu_temp()` reading from `/sys/class/thermal/thermal_zone0/temp`.
    - Add `_get_latency()` using a non-blocking ping or socket connect.
    - Add `_get_top_process()` using `psutil.process_iter()`.
- [ ] **Temporal Memory**:
    - Add a `collections.deque` buffer for the last 60 seconds of data.
    - Update `_update_state()` to analyze variance/trends in the buffer.
- [ ] **Reactive Bridge (SSE)**:
    - Add a `/events` route to the Flask app that yields JSON data.
    - Remove the meta-refresh logic from the HTML template.

## Phase 3: Frontend Implementation (Kinetic UI)
- [ ] **Glassmorphism Refresh**:
    - Update CSS with backdrop-blur and dynamic gradients based on mood.
- [ ] **GSAP Animations**:
    - Include GSAP via CDN (minimal impact).
    - Animate status changes, energy bars, and the "heartbeat" effect.
- [ ] **Live Data Listener**:
    - Add a `new EventSource('/events')` listener in the browser to update stats without reload.

## Phase 4: Verification & Deployment
- [ ] Local testing of all sensors.
- [ ] Verification of SSE stability.
- [ ] Deploy to `villa@villa.local` and restart the service.

## Tech Stack
- **Backend**: Python 3, Flask, psutil.
- **Frontend**: Vanilla HTML5, Modern CSS (Glassmorphism), GSAP.
- **Protocols**: Server-Sent Events (SSE).
