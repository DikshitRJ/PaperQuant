#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== PaperQuant Full Build Pipeline ==="
echo "Project root: $PROJECT_ROOT"
echo ""

# 1. Build Python sidecar
echo "=== Step 1/3: Building Python sidecar binary ==="
cd "$PROJECT_ROOT"
python scripts/build-sidecar.py
echo ""

# 2. Build frontend
echo "=== Step 2/3: Building React frontend ==="
cd "$PROJECT_ROOT/UI/Frontend"
npm ci
npm run build
echo ""

# 3. Build Tauri app
echo "=== Step 3/3: Building Tauri desktop app ==="
cd "$PROJECT_ROOT"
npx tauri build
echo ""

echo "=== Build complete! ==="
echo "Installers are in: $PROJECT_ROOT/src-tauri/target/release/bundle/"
