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

_voices = {}  # cache: name -> PiperVoice
_default_voice_name = None


def load_voice(model_name):
    """Load a voice model, caching for reuse."""
    from piper import PiperVoice

    if model_name in _voices:
        return _voices[model_name]

    model_path = os.path.join(MODEL_DIR, f"{model_name}.onnx")
    if not os.path.exists(model_path):
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


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
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

        voice_name = body.get("voice", None)
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
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def main():
    global _default_voice_name
    _default_voice_name = DEFAULT_MODEL
    voice = load_voice(DEFAULT_MODEL)
    if not voice:
        print(f"[error] Failed to load default model. Place .onnx files in: {MODEL_DIR}")
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
