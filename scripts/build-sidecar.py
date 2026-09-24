#!/usr/bin/env python3
"""Build the PyInstaller sidecar binary for the current platform."""

import os
import platform
import shutil
import subprocess
import sys


def get_target_triple() -> str:
    """Determine the Tauri-compatible target triple for the current platform."""
    machine = platform.machine().lower()
    system = platform.system().lower()

    arch_map = {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
    }
    arch = arch_map.get(machine, machine)

    if system == "linux":
        return f"{arch}-unknown-linux-gnu"
    elif system == "darwin":
        return f"{arch}-apple-darwin"
    elif system == "windows":
        return f"{arch}-pc-windows-msvc"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


def main() -> None:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scripts_dir = os.path.join(project_root, "scripts")
    binaries_dir = os.path.join(project_root, "src-tauri", "binaries")

    os.makedirs(binaries_dir, exist_ok=True)

    target_triple = get_target_triple()
    print(f"Building for target: {target_triple}")

    # Run PyInstaller
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            os.path.join(scripts_dir, "paperquant.spec"),
        ],
        cwd=project_root,
        check=True,
    )

    # Move binary to Tauri binaries directory with target triple suffix
    dist_dir = os.path.join(project_root, "dist")

    if platform.system() == "Windows":
        src = os.path.join(dist_dir, "paperquant-server.exe")
        dst = os.path.join(binaries_dir, f"paperquant-server-{target_triple}.exe")
    else:
        src = os.path.join(dist_dir, "paperquant-server")
        dst = os.path.join(binaries_dir, f"paperquant-server-{target_triple}")

    if os.path.exists(src):
        shutil.copy2(src, dst)
        os.chmod(dst, 0o755)
        print(f"Sidecar binary: {dst}")
    else:
        print(f"ERROR: Expected binary not found at {src}")
        sys.exit(1)

    # Clean up PyInstaller artifacts
    for d in ["build", "dist"]:
        path = os.path.join(project_root, d)
        if os.path.exists(path):
            shutil.rmtree(path)

    print("Sidecar build complete!")


if __name__ == "__main__":
    main()
