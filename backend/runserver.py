import sys
import os
import argparse
from pathlib import Path

# 1. Determine project paths reliably
CURRENT_DIR = Path(__file__).resolve().parent  # Path to backend directory (X:\NxtMov\backend)
PROJECT_ROOT = CURRENT_DIR.parent              # Path to project root (X:\NxtMov)
VENV_PYTHON = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"

# 2. Guarantee Virtual Environment Execution
# If launched with global Python instead of project venv, auto-re-execute using venv python
if VENV_PYTHON.exists():
    try:
        current_exe = Path(sys.executable).resolve()
        target_exe = VENV_PYTHON.resolve()
        if current_exe != target_exe:
            print(f"🔄 Switching to project virtual environment: {VENV_PYTHON}")
            os.execv(str(target_exe), [str(target_exe)] + sys.argv)
    except Exception as e:
        pass

# 3. Disable User-Site Package Contamination (AppData\Roaming\Python)
os.environ["PYTHONNOUSERSITE"] = "1"
try:
    import site
    site.ENABLE_USER_SITE = False
except Exception:
    pass

# Sanitize sys.path to purge any user-site package paths
sys.path = [p for p in sys.path if "AppData\\Roaming\\Python" not in p]

# Ensure backend directory is first in Python path for module resolution
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

import uvicorn

def main():
    parser = argparse.ArgumentParser(description="NxtMov Development Server Launcher")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload for development")

    args = parser.parse_args()
    reload_enabled = not args.no_reload

    print("========================================")
    print(" NxtMov Development Server")
    print("========================================")
    print(f" Python Venv: {VENV_PYTHON if VENV_PYTHON.exists() else sys.executable}")
    print(f" Backend:     http://{args.host}:{args.port}")
    print(f" API Docs:    http://{args.host}:{args.port}/docs")
    print("========================================\n")

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=reload_enabled,
        app_dir=str(CURRENT_DIR)
    )

if __name__ == "__main__":
    main()
