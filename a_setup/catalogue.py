"""
catalogue.py — Which models does this provider actually offer?

The plan says: "note which model names your provider actually offers — the
catalogue changes, and picking one now saves confusion later."

Every provider here exposes the OpenAI /models endpoint, so one call covers all
of them. GitHub Models also has a richer catalogue at /catalog/models, which
carries rate-limit tiers; we try that too when github is the active provider.
"""

import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.llm import MODEL, PROVIDER, build_client, describe


def main() -> None:
    print(describe())
    print()

    client = build_client()
    try:
        models = sorted(m.id for m in client.models.list())
    except Exception as e:
        print(f"/models not available on this provider: {type(e).__name__}: {e}")
        models = []

    if models:
        print(f"{len(models)} model(s) offered:")
        for mid in models:
            mark = "  <- current default" if mid == MODEL or MODEL.endswith(mid) else ""
            print(f"  {mid}{mark}")

    if PROVIDER == "github":
        print()
        print("GitHub Models catalogue (name / rate-limit tier):")
        try:
            r = httpx.get("https://models.github.ai/catalog/models", timeout=20)
            r.raise_for_status()
            for m in r.json():
                print(f"  {m.get('id', '?'):<40} {m.get('rate_limit_tier', '?')}")
        except Exception as e:
            print(f"  could not fetch: {type(e).__name__}: {e}")

    print()
    print("Pick one and put it in .env as LLM_MODEL=<id> to override the default.")


if __name__ == "__main__":
    main()
