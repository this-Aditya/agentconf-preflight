"""
hello.py — Day 00, step 3. One chat completion, from a file, not a notebook.

This is the smallest thing that proves the whole chain works: .env loaded, key
accepted, base_url reachable, model name valid, text came back.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.llm import ask, build_client, describe

PROMPT = "In one sentence: what is the difference between a model and an agent?"


def main() -> None:
    print(describe())
    print()
    client = build_client()
    reply = ask(client, [{"role": "user", "content": PROMPT}], max_tokens=200)
    print(f"> {PROMPT}")
    print(reply)


if __name__ == "__main__":
    main()
