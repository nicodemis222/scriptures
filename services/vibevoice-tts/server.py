"""
Scriptures VibeVoice TTS — Streaming HTTP server.
First audio chunk within ~1-2 seconds on Apple Silicon.

Endpoints:
  POST /stream     — streaming WAV (chunked transfer, plays as it generates)
  POST /synthesize — batch WAV (complete file, legacy)
  GET  /health     — server status
  GET  /voices     — available voice presets
"""

import copy
import io
import json
import os
import struct
import threading
import traceback
import wave
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import numpy as np
import torch

PORT = int(os.environ.get("TTS_PORT", "8095"))
MODEL_PATH = os.environ.get("MODEL_PATH", "microsoft/VibeVoice-Realtime-0.5B")
DEVICE = os.environ.get("TTS_DEVICE", "auto")
DEFAULT_VOICE = os.environ.get("TTS_DEFAULT_VOICE", "en-Emma_woman")
VOICES_DIR = Path(__file__).parent / "voices"
SAMPLE_RATE = 24_000
INFERENCE_STEPS = int(os.environ.get("TTS_INFERENCE_STEPS", "5"))

_service = None
_lock = threading.Lock()


def _detect_device():
    if DEVICE != "auto":
        return DEVICE
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class StreamingTTSService:
    def __init__(self, model_path, device, inference_steps=5):
        self.model_path = model_path
        self.device = device
        self.inference_steps = inference_steps
        self.sample_rate = SAMPLE_RATE
        self.model = None
        self.processor = None
        self.voice_presets = {}
        self._voice_cache = {}
        self.default_voice_key = DEFAULT_VOICE

    def load(self):
        from vibevoice.modular.modeling_vibevoice_streaming_inference import (
            VibeVoiceStreamingForConditionalGenerationInference,
        )
        from vibevoice.processor.vibevoice_streaming_processor import (
            VibeVoiceStreamingProcessor,
        )

        print(f"[startup] Loading model from {self.model_path} on {self.device}")
        self.processor = VibeVoiceStreamingProcessor.from_pretrained(self.model_path)

        if self.device == "mps":
            dtype, device_map, attn = torch.float32, None, "sdpa"
        elif self.device == "cuda":
            dtype, device_map, attn = torch.bfloat16, "cuda", "flash_attention_2"
        else:
            dtype, device_map, attn = torch.float32, "cpu", "sdpa"

        self.model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
            self.model_path, torch_dtype=dtype, device_map=device_map, attn_implementation=attn,
        )
        if self.device == "mps":
            self.model.to("mps")

        self.model.eval()
        self.model.model.noise_scheduler = self.model.model.noise_scheduler.from_config(
            self.model.model.noise_scheduler.config,
            algorithm_type="sde-dpmsolver++",
            beta_schedule="squaredcos_cap_v2",
        )
        self.model.set_ddpm_inference_steps(num_steps=self.inference_steps)

        for pt_path in VOICES_DIR.rglob("*.pt"):
            self.voice_presets[pt_path.stem] = pt_path
        print(f"[startup] {len(self.voice_presets)} voices loaded")

        if self.default_voice_key in self.voice_presets:
            self._cache_voice(self.default_voice_key)
        print("[startup] Ready!")

    def _cache_voice(self, key):
        if key in self._voice_cache:
            return self._voice_cache[key]
        pt_path = self.voice_presets.get(key)
        if not pt_path:
            return None
        cached = self.processor.from_cached_prompt(str(pt_path))
        self._voice_cache[key] = cached
        return cached

    def stream(self, text, voice_key=None):
        """Generator yielding PCM16 bytes as audio chunks are generated."""
        from vibevoice.modular.streamer import AudioStreamer

        voice_key = voice_key or self.default_voice_key
        cached = self._cache_voice(voice_key)

        inputs = self.processor.process_input_with_cached_prompt(
            text=text.strip().replace("\u2019", "'"),
            cached_prompt=cached,
            padding=True,
            return_tensors="pt",
            return_attention_mask=True,
        )
        device = torch.device(self.device)
        for k, v in inputs.items():
            if torch.is_tensor(v):
                inputs[k] = v.to(device)

        audio_streamer = AudioStreamer(batch_size=1, stop_signal=None, timeout=None)
        errors = []

        def generate():
            try:
                self.model.generate(
                    **inputs,
                    max_new_tokens=None,
                    cfg_scale=1.5,
                    tokenizer=self.processor.tokenizer,
                    generation_config={"do_sample": False},
                    audio_streamer=audio_streamer,
                    verbose=False,
                    all_prefilled_outputs=copy.deepcopy(cached) if cached else None,
                )
            except Exception as e:
                errors.append(e)
                traceback.print_exc()
                audio_streamer.end()

        thread = threading.Thread(target=generate, daemon=True)
        thread.start()

        try:
            for chunk in audio_streamer.get_stream(0):
                if torch.is_tensor(chunk):
                    chunk = chunk.detach().cpu().to(torch.float32).numpy()
                else:
                    chunk = np.asarray(chunk, dtype=np.float32)
                if chunk.ndim > 1:
                    chunk = chunk.reshape(-1)
                peak = np.max(np.abs(chunk)) if chunk.size else 0.0
                if peak > 1.0:
                    chunk = chunk / peak
                pcm16 = (np.clip(chunk, -1.0, 1.0) * 32767.0).astype(np.int16)
                yield pcm16.tobytes()
        finally:
            audio_streamer.end()
            thread.join(timeout=10)

    def synthesize_wav(self, text, voice_key=None):
        """Batch: returns complete WAV bytes."""
        pcm_parts = list(self.stream(text, voice_key))
        pcm_data = b"".join(pcm_parts)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(pcm_data)
        return buf.getvalue()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"status": "ok", "device": _service.device})
        elif self.path == "/voices":
            voices = []
            for key in sorted(_service.voice_presets.keys()):
                parts = key.split("-", 1)
                lang = parts[0] if len(parts) > 1 else "en"
                desc = parts[1] if len(parts) > 1 else key
                voices.append({"voice_id": key, "language": lang, "description": desc})
            self._json(200, voices)
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        text = body.get("text", "").strip()
        voice = body.get("voice", DEFAULT_VOICE)

        if not text:
            self.send_error(400, "Missing text")
            return

        if self.path == "/stream":
            self._stream_response(text, voice)
        elif self.path == "/synthesize":
            self._batch_response(text, voice)
        else:
            self.send_error(404)

    def _stream_response(self, text, voice):
        """Stream WAV: header first, then PCM chunks as they generate."""
        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.end_headers()

        # WAV header with unknown size (0xFFFFFFFF)
        header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF', 0x7FFFFFFF, b'WAVE',
            b'fmt ', 16, 1, 1,
            SAMPLE_RATE, SAMPLE_RATE * 2, 2, 16,
            b'data', 0x7FFFFFFF - 36,
        )
        self.wfile.write(header)
        self.wfile.flush()

        with _lock:
            try:
                for pcm_bytes in _service.stream(text, voice):
                    self.wfile.write(pcm_bytes)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception as e:
                print(f"[stream] Error: {e}")

    def _batch_response(self, text, voice):
        """Batch: return complete WAV."""
        with _lock:
            wav_data = _service.synthesize_wav(text, voice)
        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(wav_data)))
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
    global _service
    device = _detect_device()
    _service = StreamingTTSService(MODEL_PATH, device, INFERENCE_STEPS)
    _service.load()

    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[server] Listening on :{PORT} (device: {device})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[server] Shutting down")
        server.shutdown()


if __name__ == "__main__":
    main()
