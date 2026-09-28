#!/usr/bin/env bash
# Run Techmiary School Result Manager from source on Linux (for testing changes).
# First time: creates a private Python environment and installs PySide6 (needs internet once).
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -r requirements.txt
fi
.venv/bin/python app/main.py
