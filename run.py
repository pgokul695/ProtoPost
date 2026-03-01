"""
ProtoPost launcher — zero-setup entry point for desktop users.

Run with:
    python run.py           # dev / direct Python
    ./ProtoPost-linux       # compiled PyInstaller binary
    ./ProtoPost-macos
    ProtoPost-windows.exe

Configuration priority (first match wins):
  1. .env file next to executable  → loaded via python-dotenv, wizard skipped
  2. PORT already in environment   → cloud / Docker / shell export, wizard skipped
  3. init_config.json exists       → previous wizard run, re-used silently
  4. None of the above             → interactive first-run wizard
"""

import json
import os
import sys
import threading
import webbrowser

import uvicorn


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def resource_path(rel: str) -> str:
    """
    Resolve a path to a bundled read-only asset (e.g. frontend/).

    When running inside a PyInstaller one-file bundle, assets are extracted to
    sys._MEIPASS.  When running as plain Python, resolve relative to this file.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return os.path.join(meipass, rel)
    root = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(root, rel)


def data_path(filename: str) -> str:
    """
    Resolve a path for runtime data files (emails.db, config.json,
    init_config.json).

    Always resolves next to the executable / run.py, never inside the
    PyInstaller temp bundle, so data persists across launches.
    """
    return os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), filename)


# ---------------------------------------------------------------------------
# Skip-condition 1: .env file present
# ---------------------------------------------------------------------------

_env_file = data_path(".env")

if os.path.isfile(_env_file):
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        # python-dotenv not installed — parse manually so we have no hard dep
        with open(_env_file, encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _, _v = _line.partition("=")
                    os.environ.setdefault(_k.strip(), _v.strip())

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    auth_token = os.environ.get("AUTH_TOKEN", "")
    _skip_wizard = True

# ---------------------------------------------------------------------------
# Skip-condition 2: PORT already in environment (cloud / Docker / CI)
# ---------------------------------------------------------------------------

elif "PORT" in os.environ:
    port = int(os.environ["PORT"])
    host = os.environ.get("HOST", "0.0.0.0")
    auth_token = os.environ.get("AUTH_TOKEN", "")
    _skip_wizard = True

# ---------------------------------------------------------------------------
# Normal flow: check for existing init_config.json or run wizard
# ---------------------------------------------------------------------------

else:
    _init_cfg_path = data_path("init_config.json")

    if os.path.isfile(_init_cfg_path):
        # Silent reload from previous wizard run
        with open(_init_cfg_path, encoding="utf-8") as _f:
            _cfg = json.load(_f)
        port = int(_cfg.get("port", 8000))
        host = _cfg.get("host", "127.0.0.1")
        auth_token = _cfg.get("auth_token") or ""
    else:
        # ── First-run wizard ──────────────────────────────────────────────
        print()
        print("  ╔══════════════════════════════════════╗")
        print("  ║   Welcome to ProtoPost! First Setup  ║")
        print("  ╚══════════════════════════════════════╝")
        print('  This runs once. Delete init_config.json to reconfigure.')
        print()

        # Port prompt
        while True:
            raw = input("  Which port should ProtoPost run on? [default: 8000]: ").strip()
            if raw == "":
                port = 8000
                break
            try:
                port = int(raw)
                if 1024 <= port <= 65535:
                    break
                print("  Please enter a port between 1024 and 65535.")
            except ValueError:
                print("  Please enter a valid integer.")

        # Auth token prompt
        print()
        print("  ─────────────────────────────────────────────")
        print("  Auth Token (optional)")
        print("  Protects the dashboard and all /api/* endpoints with a Bearer token.")
        print("  Leave blank for no authentication — fine for local use.")
        print("  Tip: generate one with: openssl rand -hex 16")
        print("  ─────────────────────────────────────────────")
        raw_token = input("  Auth token [leave blank to skip]: ").strip()
        auth_token = raw_token if raw_token else ""

        host = "127.0.0.1"

        # Persist for future launches
        _cfg_data = {
            "port": port,
            "host": host,
            "auth_token": raw_token if raw_token else None,
        }
        with open(_init_cfg_path, "w", encoding="utf-8") as _f:
            json.dump(_cfg_data, _f, indent=2)

        print()
        print("  \u2713 Saved to init_config.json")
        print(f"  \u2713 Starting ProtoPost on port {port}...")
        print("  \u2713 Your browser will open automatically.")
        print()

    _skip_wizard = False  # (not actually used below, just for clarity)


# ---------------------------------------------------------------------------
# Inject resolved config into the environment for the backend
#
# setdefault ensures we never overwrite values already present (e.g. a .env
# file or the host platform — those take precedence).
# ---------------------------------------------------------------------------

os.environ.setdefault("PORT", str(port))
os.environ.setdefault("HOST", host)
os.environ.setdefault("AUTH_TOKEN", auth_token)

# Point the backend at data files next to the executable
os.environ.setdefault("DATABASE_PATH", data_path("emails.db"))
os.environ.setdefault("CONFIG_PATH", data_path("config.json"))

# ---------------------------------------------------------------------------
# Auto-open browser
# ---------------------------------------------------------------------------

threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{port}")).start()

# ---------------------------------------------------------------------------
# Start server
# ---------------------------------------------------------------------------

uvicorn.run("backend.main:app", host=host, port=port, reload=False)
