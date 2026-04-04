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
import time
import wave
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

PORT = int(os.environ.get("TTS_PORT", "8095"))
MODEL_DIR = os.environ.get("MODEL_DIR", str(Path(__file__).parent / "models"))
DEFAULT_MODEL = os.environ.get("TTS_MODEL", "en_US-lessac-high")

_voice = None
_voice_name = None


def load_voice(model_name=None):
    global _voice, _voice_name
    from piper import PiperVoice

    model_name = model_name or DEFAULT_MODEL
    model_path = os.path.join(MODEL_DIR, f"{model_name}.onnx")

    if not os.path.exists(model_path):
        print(f"[error] Model not found: {model_path}")
        return False

    print(f"[startup] Loading model: {model_name}")
    start = time.time()
    _voice = PiperVoice.load(model_path)
    elapsed = (time.time() - start) * 1000
    _voice_name = model_name
    print(f"[startup] Model loaded in {elapsed:.0f}ms")
    return True


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {
                "status": "ok",
                "engine": "piper",
                "model": _voice_name,
                "sample_rate": _voice.config.sample_rate if _voice else 0,
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
            self._json(200, {"voices": voices, "default": _voice_name})
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/synthesize":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        text = body.get("text", "").strip()

        if not text:
            self.send_error(400, "Missing text")
            return

        if not _voice:
            self.send_error(503, "Model not loaded")
            return

        start = time.time()
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            _voice.synthesize_wav(text, wf)
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
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def main():
    if not load_voice():
        print(f"[error] Failed to load model. Place .onnx files in: {MODEL_DIR}")
        return

    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[server] Listening on :{PORT} (model: {_voice_name})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[server] Shutting down")
        server.shutdown()


if __name__ == "__main__":
    main()
