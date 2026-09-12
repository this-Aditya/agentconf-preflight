# Setup

Getting a working LLM client before anything else, so the first real module is spent
on concepts rather than on fighting the environment.

Every provider here speaks the OpenAI API shape, so the choice costs nothing later:
switching is `base_url` + `api_key` + model name, and no module code changes. It
matters less than it looks, because MCP splits the same way — a server has no idea
which model is on the other end, so all server-side work is provider-neutral, and
only the client side names anyone.

| Provider | Cost | Catch |
|---|---|---|
| `arc` — KCL ARC-AI | free | needs the VPN |
| `github` — GitHub Models | free | `410`, mid-retirement |
| `gemini` — AI Studio key | prepay balance | a billed project has no free tier |
| `vertex` — Gemini on Vertex AI | Google Cloud credits | OAuth token, expires hourly |
| `radar` — KCL RADAR | free | not auto-picked; private base URL |

## 1. Point the OpenAI SDK at a provider

```bash
cp ../.env.example ../.env     # then fill in whichever keys you have
uv sync
uv run python a_setup/check_env.py
```

Keys live in the gitignored `.env` and load with python-dotenv. `check_env.py` makes
no network call, so it is safe to run first — it prints every provider, whether its
credentials are present, and which one won.

## 2. Install `uv`

The package manager the MCP tooling assumes. A faster drop-in for pip, and every MCP
command later starts with it. → [installation](https://docs.astral.sh/uv/getting-started/installation/)

Needs Python 3.10+; uv will install one if yours is older.

## 3. One completion, from a file

```bash
uv run python a_setup/hello.py
uv run python a_setup/catalogue.py     # what this provider offers today
```

Run the catalogue rather than trusting a model name from a tutorial. Names retire:
`gemini-2.5-flash` and `2.5-flash-lite` now return `404 no longer available to new
users`, and that is the exact model most current writing recommends.

## 4. Trigger the rate limit on purpose

```bash
uv run python a_setup/rate_limit_probe.py
```

A dozen quick calls with **no retry**, so the 429 actually lands. An agent loop spends
one request per turn, so on a tightly limited free tier a five-turn debug session is
half your minute — and the 429 that follows looks exactly like a bug if you have never
seen one deliberately.

## Done when

One successful call, `uv --version` printing, and you have seen a 429 on purpose.
