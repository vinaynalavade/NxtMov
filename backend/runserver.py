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
            print(f"[VENV] Activating virtual environment: {VENV_PYTHON}")
            os.execv(str(target_exe), [str(target_exe)] + sys.argv)
    except Exception:
        pass

# 3. Disable User-Site Package Contamination
os.environ["PYTHONNOUSERSITE"] = "1"
try:
    import site
    site.ENABLE_USER_SITE = False
except Exception:
    pass

# Purge any user-site package paths
sys.path = [p for p in sys.path if "AppData\\Roaming\\Python" not in p]

# Ensure backend directory is first in Python path for module resolution
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

# 4. Pre-flight dependency check
missing_deps = []
for pkg in ["fastapi", "uvicorn", "pydantic", "sqlalchemy", "jose", "passlib"]:
    try:
        __import__(pkg)
    except ImportError:
        missing_deps.append(pkg)

if missing_deps:
    print("\n[ERROR] Missing required Python dependencies:")
    for dep in missing_deps:
        print(f"   - {dep}")
    print("\nPlease install the required dependencies using:")
    print("   pip install -r requirements.txt\n")
    sys.exit(1)

import uvicorn

def main():
    parser = argparse.ArgumentParser(description="NxtMov Backend Server Launcher")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")

    args = parser.parse_args()
    reload_enabled = not args.no_reload

    backend_url = f"http://{args.host}:{args.port}"

    print("\n========================================================")
    print(" [*] NxtMov Backend Server")
    print("========================================================")
    print(f" - Backend API:    {backend_url}")
    print(f" - API Docs:       {backend_url}/docs")
    print(f" - Health Check:   {backend_url}/api/v1/health")
    print(f" - Python Runtime: {sys.executable}")
    print(f" - CORS Origins:   http://127.0.0.1:5500, http://localhost:5500 (Live Server)")
    print("========================================================\n")

    try:
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=reload_enabled,
            app_dir=str(CURRENT_DIR)
        )
    except Exception as e:
        print(f"\n❌ [NxtMov Server Error] Failed to start server on {backend_url}: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
