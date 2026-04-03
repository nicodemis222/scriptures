# PyInstaller spec for VibeVoice TTS server
# Bundles the streaming server + all dependencies into a single executable

import sys
from pathlib import Path

block_cipher = None

# Find vibevoice package
import vibevoice
vibevoice_path = Path(vibevoice.__file__).parent

a = Analysis(
    ['server.py'],
    pathex=[],
    binaries=[],
    datas=[
        (str(vibevoice_path), 'vibevoice'),
        ('voices', 'voices'),
    ],
    hiddenimports=[
        'vibevoice',
        'vibevoice.modular',
        'vibevoice.modular.streamer',
        'vibevoice.modular.modeling_vibevoice_streaming_inference',
        'vibevoice.processor',
        'vibevoice.processor.vibevoice_streaming_processor',
        'torch',
        'transformers',
        'diffusers',
        'numpy',
        'scipy',
        'librosa',
        'accelerate',
        'safetensors',
        'huggingface_hub',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['gradio', 'matplotlib', 'tkinter', 'PIL', 'IPython'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='vibevoice-tts',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    target_arch='arm64',
)
