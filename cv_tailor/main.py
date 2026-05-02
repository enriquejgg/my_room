"""
CV Tailor — Smart CV Optimiser
Entry point for the application.

Run with:
    python main.py

Requirements:
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm  (optional, for better NER)

Environment Variables (optional):
    ANTHROPIC_API_KEY   — pre-fills the API key in AI mode
"""
import sys
import os
from pathlib import Path

# ── Project root on path ──────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── macOS + Python 3.13/3.14 tkinter fix ────────────────────────────────────
# Silence deprecation warnings that can cause silent exits on macOS
if sys.platform == "darwin":
    os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")

# ── Load .env ─────────────────────────────────────────────────────────────────
def _load_env():
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        print(f"[.env] No .env file found at {env_path}")
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path, override=True)
        print(f"[.env] Loaded from {env_path}")
        if os.environ.get("ANTHROPIC_API_KEY"):
            print("[.env] ANTHROPIC_API_KEY found ✓")
        else:
            print("[.env] Warning: ANTHROPIC_API_KEY not set in .env")
    except ImportError:
        print("[.env] python-dotenv not installed, parsing .env manually…")
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key:
                    os.environ[key] = value
        if os.environ.get("ANTHROPIC_API_KEY"):
            print("[.env] ANTHROPIC_API_KEY found ✓")

_load_env()


# ── Dependency check ──────────────────────────────────────────────────────────
def check_dependencies() -> bool:
    """
    Check required packages. Returns True if all critical deps are present.
    Prints warnings for missing optional deps.
    Does NOT use input() — safe for PyCharm / non-interactive runners.
    """
    missing_critical = []
    missing_optional = []

    for pkg, import_name in [("pdfplumber", "pdfplumber"),
                               ("reportlab",  "reportlab")]:
        try:
            __import__(import_name)
        except ImportError:
            missing_critical.append(pkg)

    for pkg, import_name in [("scikit-learn", "sklearn"),
                               ("anthropic",   "anthropic")]:
        try:
            __import__(import_name)
        except ImportError:
            missing_optional.append(pkg)

    if missing_optional:
        print("Optional packages not installed (non-critical):")
        for pkg in missing_optional:
            print(f"  pip install {pkg}")

    if missing_critical:
        print("\n" + "=" * 60)
        print("MISSING REQUIRED PACKAGES — install before running:")
        for pkg in missing_critical:
            print(f"  pip install {pkg}")
        print("\nOr install everything at once:")
        print("  pip install -r requirements.txt")
        print("=" * 60 + "\n")
        return False   # caller will show GUI error instead of input()

    return True


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    deps_ok = check_dependencies()

    try:
        import tkinter as tk
    except ImportError:
        print("FATAL: tkinter is not installed for this Python.")
        print("On macOS: reinstall Python from python.org (Framework build).")
        print("On Linux: sudo apt install python3-tk")
        sys.exit(1)

    if not deps_ok:
        # Show a minimal Tk error window instead of blocking input()
        root = tk.Tk()
        root.withdraw()
        from tkinter import messagebox
        messagebox.showerror(
            "Missing Dependencies",
            "Required packages are not installed.\n\n"
            "Run in terminal:\n  pip install -r requirements.txt\n\n"
            "Then restart the application."
        )
        root.destroy()
        sys.exit(1)

    try:
        from ui.app import CVTailorApp
        app = CVTailorApp()

        # ── macOS focus fix ───────────────────────────────────────────────────
        # On macOS, windows launched from a terminal/IDE don't automatically
        # receive focus. Force the window to the front.
        if sys.platform == "darwin":
            app.lift()
            app.focus_force()
            app.after(100, lambda: app.lift())  # re-lift after 100 ms

        app.mainloop()

    except Exception as e:
        print(f"\nFatal error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()