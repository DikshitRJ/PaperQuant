# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collect all hidden imports for complex packages
zmq_datas, zmq_binaries, zmq_hiddenimports = collect_all("zmq")
yfinance_datas, yfinance_binaries, yfinance_hiddenimports = collect_all("yfinance")

a = Analysis(
    ["../api_server.py"],
    pathex=[".."],
    binaries=zmq_binaries + yfinance_binaries,
    datas=[
        ("../Indicators", "Indicators"),  # Include indicators package
        ("../Price_adapter", "Price_adapter"),  # Include price adapter
        ("../Trade_adapter.py", "."),  # Include trade adapter
        ("../Handler.py", "."),  # Include handler
        ("../api", "api"),  # Include API package
    ]
    + zmq_datas
    + yfinance_datas,
    hiddenimports=[
        "diskcache",
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "fastapi",
        "starlette",
        "pydantic",
        "websockets",
        "numpy",
        "pandas",
        "sqlite3",
        "multipart",
        "python_multipart",
    ]
    + zmq_hiddenimports
    + yfinance_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["jupyter", "notebook", "ipython", "tkinter", "matplotlib"],
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
    name="paperquant-server",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to avoid ZMQ issues
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Console mode for stdout port discovery
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
