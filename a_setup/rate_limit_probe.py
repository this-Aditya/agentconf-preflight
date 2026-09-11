"""
rate_limit_probe.py — Hit the rate limit on purpose.

Why: an agent loop spends one request per turn. On GitHub Models' free tier
(~10 requests/minute) a five-turn debug session is half your minute, and the 429
that follows looks exactly like a bug if you have never seen it before. See it
once now, in a script that expects it, and you will recognise it in a loop later.

This deliberately does NOT use shared.llm.ask(), because ask() retries through
rate limits — which is what you want in a lesson and precisely what you do not
want here. We call the SDK directly and let the 429 land.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openai import RateLimitError

from shared.llm import MODEL, PROVIDER, build_client, describe

BURST = 12
MESSAGES = [{"role": "user", "content": "Reply with the single word: ok"}]


def main() -> None:
    print(describe())
    print()
    if PROVIDER in {"radar", "arc"}:
        print(f"note: '{PROVIDER}' is not tightly rate-limited, so you may see no 429 here.")
        print("      Run it once with LLM_PROVIDER=github to see what one looks like.")
        print()

    client = build_client()
    limited_at = None
    started = time.monotonic()

    for i in range(1, BURST + 1):
        t0 = time.monotonic()
        try:
            resp = client.chat.completions.create(
                model=MODEL, messages=MESSAGES, max_tokens=5, temperature=0
            )
            text = (resp.choices[0].message.content or "").strip()
            print(f"{i:>3}. {time.monotonic() - t0:5.2f}s  ok    {text!r}")
        except RateLimitError as e:
            limited_at = limited_at or i
            print(f"{i:>3}. {time.monotonic() - t0:5.2f}s  429   {_one_line(e)}")
        except Exception as e:
            print(f"{i:>3}. {time.monotonic() - t0:5.2f}s  {type(e).__name__}: {_one_line(e)}")

    print()
    elapsed = time.monotonic() - started
    if limited_at:
        print(f"Rate limited from request {limited_at} of {BURST}, after {elapsed:.1f}s.")
        print("That is the error to recognise tomorrow. Two ways to live with it:")
        print("  - pace the loop: sleep 60/limit seconds between turns")
        print("  - or retry with backoff, which is what shared.llm.ask() already does")
    else:
        print(f"No 429 in {BURST} requests over {elapsed:.1f}s — this provider has room.")
        print("Still worth knowing the shape: a 429 is what you get when it does not.")


def _one_line(e: Exception) -> str:
    return " ".join(str(e).split())[:160]


if __name__ == "__main__":
    main()
