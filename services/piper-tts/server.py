"""
Scriptures Piper TTS — Fast HTTP server.
Synthesis in ~200ms per sentence. No gaps in continuous reading.

Endpoints:
  POST /synthesize — synthesize text to WAV
  GET  /health     — server status
  GET  /voices     — available voice models
"""

import io
import json
import os
import re
import socketserver
import time
import wave
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

PORT = int(os.environ.get("TTS_PORT", "8095"))
MODEL_DIR = os.environ.get("MODEL_DIR", str(Path(__file__).parent / "models"))
DEFAULT_MODEL = os.environ.get("TTS_MODEL", "en_US-lessac-high")

# Request hardening limits.
MAX_BODY_BYTES = 64 * 1024      # reject request bodies larger than 64 KB
MAX_TEXT_CHARS = 5000           # cap synthesis input length
VOICE_RE = re.compile(r"^[A-Za-z0-9_\-]+$")  # safe voice-id charset
ALLOWED_HOSTS = {"127.0.0.1", "localhost"}

_voices = {}  # cache: name -> PiperVoice
_default_voice_name = None


def _safe_voice_name(name):
    """Validate a voice id and ensure the resolved path stays inside MODEL_DIR.
    Returns the model path, or None if the name is unsafe / escapes MODEL_DIR."""
    if not name or not VOICE_RE.match(name):
        return None
    model_path = os.path.join(MODEL_DIR, f"{name}.onnx")
    real_model = os.path.realpath(model_path)
    real_dir = os.path.realpath(MODEL_DIR)
    if not real_model.startswith(real_dir + os.sep):
        return None
    return model_path


def load_voice(model_name):
    """Load a voice model, caching for reuse."""
    from piper import PiperVoice

    if model_name in _voices:
        return _voices[model_name]

    model_path = _safe_voice_name(model_name)
    if not model_path or not os.path.exists(model_path):
        return None

    print(f"[load] Loading model: {model_name}")
    start = time.time()
    voice = PiperVoice.load(model_path)
    elapsed = (time.time() - start) * 1000
    _voices[model_name] = voice
    print(f"[load] {model_name} loaded in {elapsed:.0f}ms")
    return voice


def get_voice(requested_name=None):
    """Get a voice by name, falling back to default."""
    name = requested_name or _default_voice_name or DEFAULT_MODEL
    voice = load_voice(name)
    if voice:
        return voice, name
    # Fall back to default
    if name != DEFAULT_MODEL:
        voice = load_voice(DEFAULT_MODEL)
        if voice:
            return voice, DEFAULT_MODEL
    return None, None


class NoFQDNServer(socketserver.ThreadingMixIn, HTTPServer):
    """Threaded HTTPServer that skips socket.getfqdn() in server_bind.
    getfqdn() can hang for 30+ seconds on some macOS DNS configurations.
    ThreadingMixIn prevents a single slow client from blocking all TTS."""
    daemon_threads = True

    def server_bind(self):
        socketserver.TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = host or "localhost"
        self.server_port = port


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _host_ok(self):
        """Reject requests whose Host header isn't loopback (blocks DNS-rebinding
        attacks from a browser pointing a hostname at 127.0.0.1)."""
        host = self.headers.get("Host", "")
        hostname = host.split(":")[0]
        if hostname and hostname not in ALLOWED_HOSTS:
            self.send_error(403, "Forbidden host")
            return False
        return True

    def do_GET(self):
        if not self._host_ok():
            return
        if self.path == "/health":
            default_voice, _ = get_voice()
            self._json(200, {
                "status": "ok",
                "engine": "piper",
                "model": _default_voice_name,
                "voices_loaded": len(_voices),
                "sample_rate": default_voice.config.sample_rate if default_voice else 0,
            })
        elif self.path == "/voices":
            voices = []
            if os.path.isdir(MODEL_DIR):
                for f in sorted(os.listdir(MODEL_DIR)):
                    if f.endswith(".onnx"):
                        name = f.replace(".onnx", "")
                        parts = name.split("-")
                        lang = parts[0] if parts else "en"
                        voices.append({
                            "id": name,
                            "name": name.replace("_", " ").replace("-", " ").title(),
                            "language": lang,
                            "description": name,
                        })
            self._json(200, {"voices": voices, "default": _default_voice_name})
        else:
            self.send_error(404)

    def do_POST(self):
        if not self._host_ok():
            return
        if self.path != "/synthesize":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
        except (TypeError, ValueError):
            self.send_error(400, "Bad Content-Length")
            return
        if length <= 0:
            self.send_error(400, "Missing body")
            return
        if length > MAX_BODY_BYTES:
            self.send_error(413, "Request body too large")
            return

        try:
            body = json.loads(self.rfile.read(length))
        except (ValueError, json.JSONDecodeError):
            self.send_error(400, "Invalid JSON")
            return

        text = body.get("text", "")
        if not isinstance(text, str):
            self.send_error(400, "text must be a string")
            return
        text = text.strip()[:MAX_TEXT_CHARS]
        if not text:
            self.send_error(400, "Missing text")
            return

        voice_name = body.get("voice", None)
        if voice_name is not None and not (isinstance(voice_name, str) and VOICE_RE.match(voice_name)):
            self.send_error(400, "Invalid voice id")
            return
        voice, used_name = get_voice(voice_name)
        if not voice:
            self.send_error(503, "No voice model available")
            return

        start = time.time()
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            voice.synthesize_wav(text, wf)
        wav_data = buf.getvalue()
        elapsed = (time.time() - start) * 1000

        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(wav_data)))
        self.send_header("X-Synthesis-Time-Ms", str(int(elapsed)))
        self.end_headers()
        self.wfile.write(wav_data)

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        # This is a loopback-only service consumed by the app's Rust backend via
        # curl (which ignores CORS). We intentionally do NOT emit a wildcard
        # Access-Control-Allow-Origin, so a web page in a browser cannot drive
        # the synth endpoint (defends against local DNS-rebinding / CSRF).
        if not self._host_ok():
            return
        self.send_response(204)
        self.end_headers()


def main():
    global _default_voice_name
    _default_voice_name = DEFAULT_MODEL
    voice = load_voice(DEFAULT_MODEL)
    if not voice:
        print(f"[error] Failed to load default model. Place .onnx files in: {MODEL_DIR}")
        return

    server = NoFQDNServer(("127.0.0.1", PORT), Handler)
    print(f"[server] Listening on :{PORT} (model: {_default_voice_name})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[server] Shutting down")
        server.shutdown()


if __name__ == "__main__":
    main()
