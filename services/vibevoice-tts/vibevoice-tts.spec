# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['server.py'],
    pathex=[],
    binaries=[],
    datas=[('voices', 'voices')],
    hiddenimports=['vibevoice', 'vibevoice.modular', 'vibevoice.modular.streamer', 'vibevoice.modular.modeling_vibevoice_streaming_inference', 'vibevoice.processor', 'vibevoice.processor.vibevoice_streaming_processor', 'torch', 'transformers', 'diffusers', 'numpy', 'scipy', 'accelerate', 'safetensors'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['gradio', 'matplotlib', 'tkinter', 'PIL'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='vibevoice-tts',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
