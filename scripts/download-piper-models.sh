#!/usr/bin/env bash
# Download Piper TTS ONNX voice models from HuggingFace
set -e

MODELS_DIR="$(cd "$(dirname "$0")/../services/piper-tts/models" && pwd)"
BASE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en"

# Resolve HuggingFace IP via Google DNS to avoid local DNS filtering
HF_IP=$(dig +short huggingface.co @8.8.8.8 | head -1)
RESOLVE_FLAG=""
if [ -n "$HF_IP" ]; then
  RESOLVE_FLAG="--resolve huggingface.co:443:${HF_IP}"
fi

VOICES="en_US-lessac-high:en_US/lessac/high
en_GB-cori-high:en_GB/cori/high
en_US-amy-medium:en_US/amy/medium
en_US-joe-medium:en_US/joe/medium"

echo "Downloading Piper voice models to: $MODELS_DIR"
mkdir -p "$MODELS_DIR"

echo "$VOICES" | while IFS=: read -r voice path; do
  onnx_file="$MODELS_DIR/${voice}.onnx"

  if [ -f "$onnx_file" ]; then
    size=$(stat -f%z "$onnx_file" 2>/dev/null || stat -c%s "$onnx_file" 2>/dev/null)
    if [ "$size" -gt 1000000 ]; then
      echo "  [skip] ${voice}.onnx already exists ($(( size / 1048576 )) MB)"
      continue
    fi
  fi

  echo "  [download] ${voice}.onnx ..."
  curl -kL $RESOLVE_FLAG --progress-bar -o "$onnx_file" "${BASE_URL}/${path}/${voice}.onnx"

  size=$(stat -f%z "$onnx_file" 2>/dev/null || stat -c%s "$onnx_file" 2>/dev/null)
  if [ "$size" -lt 1000000 ]; then
    echo "  [error] ${voice}.onnx is too small (${size} bytes), download may have failed"
    rm -f "$onnx_file"
    exit 1
  fi
  echo "  [ok] ${voice}.onnx ($(( size / 1048576 )) MB)"
done

echo "All voice models downloaded successfully."
