"""
check_env.py — Answers one question: what will actually run?

Prints every provider, whether its credentials are present, and which one
shared/llm.py has chosen. Makes no network call, so it is safe to run first.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# name -> (env vars that must all be set, what it costs you)
PROVIDERS = {
    "gemini": (["AGENTIC_AI_LEARNING_GEMINI_KEY"], "free tier, no VPN"),
    "vertex": (["VERTEX_PROJECT"], "spends Google Cloud credits"),
    "radar":  (["RADAR_OPEN_MODEL_KEY", "RADAR_OPEN_MODEL_BASE_URL"], "free, unlimited"),
    "arc":    (["KCL_AI_MODEL_API_KEY"], "free, needs VPN"),
    "github": (["AGENTIC_AI_LEARNING_GH_TOKEN"], "free, ~10 req/min"),
}


def main() -> int:
    print(f"python       {sys.version.split()[0]}")
    print(f"uv           {_uv_version()}")
    print(f".env         {'found' if (ROOT / '.env').exists() else 'MISSING — cp .env.example .env'}")
    print()

    print("provider   credentials  cost")
    print("-" * 52)
    for name, (needed, cost) in PROVIDERS.items():
        missing = [v for v in needed if not os.environ.get(v, "").strip()]
        state = "ok         " if not missing else "missing    "
        print(f"{name:<10} {state}  {cost}")
        for var in missing:
            print(f"{'':<10} {'':<12}   need {var}")
    print()

    forced = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if forced:
        print(f"LLM_PROVIDER is set, so '{forced}' is forced.")

    # Import last: llm.py resolves the provider at import time and will exit
    # with a clear message if nothing is usable.
    sys.path.insert(0, str(ROOT))
    from shared.llm import describe

    print("chosen:", describe())
    if os.environ.get("VERTEX_PROJECT") and not os.environ.get("VERTEX_ACCESS_TOKEN"):
        print()
        print("note: vertex will shell out to `gcloud auth print-access-token`.")
        print("      That token expires after about an hour.")
    return 0


def _uv_version() -> str:
    if not shutil.which("uv"):
        return "NOT INSTALLED — https://docs.astral.sh/uv/getting-started/installation/"
    out = subprocess.run(["uv", "--version"], capture_output=True, text=True)
    return out.stdout.strip() or "?"


if __name__ == "__main__":
    raise SystemExit(main())
