"""
ARK VibeVoice TTS — HTTP wrapper around Microsoft VibeVoice-Realtime-0.5B.
Returns WAV audio from text input with 9 selectable voice presets.
Serves /synthesize, /health, and /voices endpoints.
"""

import copy
import io
import json
import os
import threading
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

# Global state
_model = None
_processor = None
_voice_cache = {}
_voice_presets = {}
_lock = threading.Lock()


def _detect_device():
    """Pick the best available device."""
    if DEVICE != "auto":
        return DEVICE
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_model():
    """Load VibeVoice model and processor once at startup."""
    global _model, _processor, _voice_presets

    from vibevoice.modular.modeling_vibevoice_streaming_inference import (
        VibeVoiceStreamingForConditionalGenerationInference,
    )
    from vibevoice.processor.vibevoice_streaming_processor import (
        VibeVoiceStreamingProcessor,
    )

    device = _detect_device()
    print(f"[TTS] Loading VibeVoice model from {MODEL_PATH} on {device}")

    _processor = VibeVoiceStreamingProcessor.from_pretrained(MODEL_PATH)

    # Device-specific settings
    if device == "cuda":
        dtype, device_map, attn = torch.bfloat16, "cuda", "flash_attention_2"
    elif device == "mps":
        dtype, device_map, attn = torch.float32, None, "sdpa"
    else:
        dtype, device_map, attn = torch.float32, "cpu", "sdpa"

    try:
        _model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
            MODEL_PATH, torch_dtype=dtype, device_map=device_map, attn_implementation=attn,
        )
    except Exception:
        if attn == "flash_attention_2":
            print("[TTS] Flash Attention unavailable, falling back to SDPA")
            _model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
                MODEL_PATH, torch_dtype=dtype, device_map=device_map, attn_implementation="sdpa",
            )
        else:
            raise

    if device == "mps":
        _model.to("mps")

    _model.eval()
    _model.set_ddpm_inference_steps(num_steps=INFERENCE_STEPS)

    # Load voice presets
    _voice_presets = {}
    for pt_path in sorted(VOICES_DIR.glob("*.pt")):
        _voice_presets[pt_path.stem] = pt_path
    print(f"[TTS] Loaded {len(_voice_presets)} voice presets: {list(_voice_presets.keys())}")
    print(f"[TTS] Default voice: {DEFAULT_VOICE}")

    # Pre-cache default voice
    _get_voice(DEFAULT_VOICE)
    print(f"[TTS] Model ready on {device}")


def _get_voice(key):
    """Load and cache a voice preset tensor."""
    if key not in _voice_presets:
        key = DEFAULT_VOICE
    if key not in _voice_cache:
        device = _detect_device()
        torch_device = torch.device(device)
        _voice_cache[key] = torch.load(
            _voice_presets[key], map_location=torch_device, weights_only=False,
        )
    return _voice_cache[key]


def synthesize(text, voice_key=None):
    """Synthesize text to WAV bytes using VibeVoice (batch mode)."""
    if not voice_key or voice_key not in _voice_presets:
        voice_key = DEFAULT_VOICE

    device = _detect_device()
    torch_device = torch.device(device)
    prefilled = _get_voice(voice_key)

    inputs = _processor.process_input_with_cached_prompt(
        text=text.strip().replace("\u2019", "'"),
        cached_prompt=prefilled,
        padding=True,
        return_tensors="pt",
        return_attention_mask=True,
    )
    # Move tensors to device
    for k, v in inputs.items():
        if torch.is_tensor(v):
            inputs[k] = v.to(torch_device)

    with _lock:
        outputs = _model.generate(
            **inputs,
            max_new_tokens=None,
            cfg_scale=1.5,
            tokenizer=_processor.tokenizer,
            generation_config={"do_sample": False},
            verbose=True,
            all_prefilled_outputs=copy.deepcopy(prefilled),
        )

    # Extract audio
    if not outputs.speech_outputs or outputs.speech_outputs[0] is None:
        raise RuntimeError("No audio generated")

    audio = outputs.speech_outputs[0]
    if torch.is_tensor(audio):
        audio = audio.detach().cpu().to(torch.float32).numpy()
    else:
        audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.reshape(-1)

    # Normalize
    peak = np.max(np.abs(audio)) if audio.size else 0.0
    if peak > 1.0:
        audio = audio / peak

    # Encode as WAV
    pcm = (np.clip(audio, -1.0, 1.0) * 32767.0).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


# Voice metadata for the frontend
VOICE_META = {
    "en-Carter_man":  {"name": "Carter",  "language": "en", "gender": "male",   "description": "Deep authoritative male"},
    "en-Davis_man":   {"name": "Davis",   "language": "en", "gender": "male",   "description": "Clear professional male"},
    "en-Emma_woman":  {"name": "Emma",    "language": "en", "gender": "female", "description": "Natural warm female"},
    "en-Frank_man":   {"name": "Frank",   "language": "en", "gender": "male",   "description": "Steady calm male"},
    "en-Grace_woman": {"name": "Grace",   "language": "en", "gender": "female", "description": "Elegant poised female"},
    "en-Mike_man":    {"name": "Mike",    "language": "en", "gender": "male",   "description": "Casual friendly male"},
    "sp-Spk0_woman":  {"name": "Sofia",   "language": "es", "gender": "female", "description": "Spanish female"},
    "fr-Spk0_man":    {"name": "Laurent", "language": "fr", "gender": "male",   "description": "French male"},
    "de-Spk0_man":    {"name": "Klaus",   "language": "de", "gender": "male",   "description": "German male"},
}


class TTSHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/synthesize":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                data = json.loads(body) if body else {}
                text = data.get("text", "").strip()

                if not text:
                    self.send_error(400, "Missing 'text' field")
                    return

                voice = data.get("voice", DEFAULT_VOICE)
                wav_data = synthesize(text, voice)

                self.send_response(200)
                self.send_header("Content-Type", "audio/wav")
                self.send_header("Content-Length", str(len(wav_data)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(wav_data)

            except Exception as e:
                print(f"[TTS] Error: {e}")
                self.send_error(500, str(e))
        else:
            self.send_error(404)

    def do_GET(self):
        if self.path == "/health":
            ok = _model is not None and _processor is not None
            self.send_response(200 if ok else 503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok" if ok else "loading",
                "model": "VibeVoice-Realtime-0.5B",
                "voices": len(_voice_presets),
                "device": _detect_device(),
            }).encode())
        elif self.path == "/voices":
            voices = []
            for key in sorted(_voice_presets.keys()):
                meta = VOICE_META.get(key, {"name": key})
                voices.append({"id": key, **meta})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "voices": voices,
                "default": DEFAULT_VOICE,
            }).encode())
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        print(f"[TTS] {args[0]}")


if __name__ == "__main__":
    print(f"[TTS] ARK VibeVoice TTS starting on port {PORT}")
    print(f"[TTS] Model: {MODEL_PATH}")
    print(f"[TTS] Device: {_detect_device()}")
    try:
        load_model()
    except Exception as e:
        print(f"[TTS] Warning: Could not pre-load model: {e}")
    server = HTTPServer(("0.0.0.0", PORT), TTSHandler)
    server.serve_forever()
