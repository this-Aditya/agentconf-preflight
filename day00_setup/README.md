# Day 00 — Before you start: setup on your own stack

**45 min.** Not a study day — the half hour that stops Day 01 being a bad evening.

The plan as written assumes GitHub Models via the OpenAI SDK. You have more options
than that, and they all speak the same OpenAI API shape, so the choice costs you
nothing later: every MCP server you build from Day 03 is provider-neutral anyway —
an MCP server has no idea which model is on the other end. Only the client side
names anyone.

Resolution order in `shared/llm.py` (override with `LLM_PROVIDER`):

| # | Provider | Cost | Catch |
|---|---|---|---|
| 1 | `gemini` — AI Studio key | free tier | `gemini-2.5-flash-lite` only; 2.0-flash returns 429 |
| 2 | `vertex` — Gemini on Vertex AI | your GCP credits | OAuth token expires ~1 h, no static key |
| 3 | `radar` — KCL RADAR | free, unlimited | private base URL, lives in `.env` |
| 4 | `arc` — KCL ARC-AI | free | needs the VPN |
| 5 | `github` — GitHub Models | free | **~10 requests/minute** |

The one thing to know before you hit it mid-lesson: an agent loop spends a request
per turn, so on GitHub Models a five-turn debug session is half your minute. That is
a pacing annoyance, not a blocker, but it looks like a bug if nobody warns you.
Step 4 below makes you hit it on purpose.

## Steps

### 1. Build · 15 min — point the OpenAI SDK at your provider

Same library, two changed arguments: your key as `api_key`, the provider's endpoint
as `base_url`. Nothing else in the SDK changes.

```bash
cp ../.env.example ../.env      # then fill in whichever keys you have
uv sync
uv run python day00_setup/check_env.py
```

Your keys can be pasted straight across from `../agent-sandbox/4.tool-calling/.env` —
the variable names are deliberately identical.

**Exactly what:** keep the token in the gitignored `.env` and load it with
python-dotenv, the way your other projects already do. `shared/llm.py` does this for you.

### 2. Build · 15 min — install `uv`

The Python package manager the MCP tooling assumes. If you have only used pip, this
is new — a faster drop-in, and every MCP command from Day 03 starts with it.

→ [uv — installation](https://docs.astral.sh/uv/getting-started/installation/)

**Exactly what:** just the install. You need Python 3.10 or newer; uv will install
one for you if yours is older. (Already present on this machine: `uv 0.11.26`.)

### 3. Prove · 10 min — one chat completion from a Python file

```bash
uv run python day00_setup/hello.py
uv run python day00_setup/catalogue.py     # which models this provider offers you
```

**Exactly what:** note which model names your provider actually offers — the
catalogue changes, and picking one now saves confusion on Day 01.

### 4. Prove · 5 min — trigger the rate limit on purpose

```bash
uv run python day00_setup/rate_limit_probe.py
```

A dozen quick calls so you see the 429 for yourself and recognise it later.

## Paste this to start Day 00

```
I'm starting a 10-day study plan and want my environment ready first.
I can use Google Gemini (AI Studio key), Gemini via Vertex AI (I have Google
Cloud credits), KCL RADAR/ARC, or GitHub Models - all through the OpenAI Python
SDK. My keys are in a gitignored .env loaded with python-dotenv.

Walk me through: picking the provider, checking which models its catalogue
currently offers me, confirming my Python version, and making one successful
call from a Python file.

Then have me deliberately trigger the free-tier rate limit so I know what it
looks like, and tell me how to pace an agent loop around it.

Check each step actually worked before moving on.
```

## Done when

One successful call through your chosen provider, `uv --version` printing, and you
have seen a 429 on purpose.

## Makes these readable

Nothing directly. It stops Day 01 being a fight with your environment instead of
the concepts.
