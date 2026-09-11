"""
llm.py — one shared place to build the LLM client for every module.

Adapted from ../agent-sandbox/4.tool-calling/_llm.py, which already proved the
idea: we use the OpenAI SDK for EVERY provider, because all of them speak the
OpenAI API "shape". Switching provider is a change of three things — base_url,
api_key, model name. Nothing in any lesson changes.

WHICH PROVIDER GETS USED
    1. LLM_PROVIDER=gemini|vertex|radar|arc|github   -> forces that one
    2. else the first one whose credentials are present, in this order:
       gemini (free, no VPN) -> vertex (spends GCP credits) -> radar -> arc -> github

Every exercise does:
    from shared.llm import build_client, ask, MODEL, PROVIDER
"""

import os
import re
import subprocess
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import (
    OpenAI,
    AsyncOpenAI,
    BadRequestError,
    RateLimitError,
    InternalServerError,
    APITimeoutError,
    APIConnectionError,
)

# Load the .env at the repo root (one above this file's folder).
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Matches a full <think>...</think> reasoning block from "thinking" models.
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

# Gemini via the AI Studio key. On the free tier gemini-2.0-flash* return 429
# ("quota limit: 0") and the bigger thinking models can spend a small
# max_tokens budget on hidden reasoning and return EMPTY text.
# gemini-2.5-flash-lite has free quota and returns text directly.
_GEMINI = {
    "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "key_env": "AGENTIC_AI_LEARNING_GEMINI_KEY",
    "model": "gemini-2.5-flash-lite",
}

# Gemini via Vertex AI — the route that spends Google Cloud credits. Same
# OpenAI shape, but api_key is a short-lived OAuth token, not a static key.
_VERTEX = {
    "base_url": "",   # built in _resolve(), needs project + location
    "key_env": "VERTEX_ACCESS_TOKEN",
    "model": "google/gemini-2.5-flash",
}

# KCL RADAR: OpenAI-compatible, effectively unlimited, reachable without VPN.
# qwen3-30b is a thinking model, so ask() strips its <think> block.
# The base URL is a PRIVATE KCL endpoint, so it lives in .env, not in git.
_RADAR = {
    "base_url": os.environ.get("RADAR_OPEN_MODEL_BASE_URL", ""),
    "key_env": "RADAR_OPEN_MODEL_KEY",
    "model": "qwen3-30b",
}

# KCL ARC-AI — first choice. Needs the VPN.
_ARC = {
    "base_url": "https://ai.create.kcl.ac.uk/api/v1",
    "key_env": "KCL_AI_MODEL_API_KEY",
    "model": "arc:lite",
}

# GitHub Models — the fallback. Free, but ~10 requests/minute, and an agent
# loop spends a request per turn, so a five-turn debug is half your minute.
_GITHUB = {
    "base_url": "https://models.github.ai/inference",
    "key_env": "AGENTIC_AI_LEARNING_GH_TOKEN",
    "model": "openai/gpt-4o-mini",
}

_PROVIDERS = {
    "gemini": _GEMINI,
    "vertex": _VERTEX,
    "radar": _RADAR,
    "arc": _ARC,
    "github": _GITHUB,
}


def _vertex_token() -> str:
    """Vertex has no static key. Use VERTEX_ACCESS_TOKEN, else ask gcloud."""
    token = os.environ.get("VERTEX_ACCESS_TOKEN", "").strip()
    if token:
        return token
    try:
        out = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True, text=True, timeout=20, check=True,
        )
        return out.stdout.strip()
    except Exception:
        return ""


def _prepare_vertex() -> dict:
    """Fill in Vertex's base_url and key from project/location + gcloud."""
    project = os.environ.get("VERTEX_PROJECT", "").strip()
    location = os.environ.get("VERTEX_LOCATION", "us-central1").strip()
    cfg = dict(_VERTEX)
    if project:
        cfg["base_url"] = (
            f"https://{location}-aiplatform.googleapis.com/v1/"
            f"projects/{project}/locations/{location}/endpoints/openapi"
        )
    return cfg


def _usable(name: str, cfg: dict) -> bool:
    if name == "vertex":
        return bool(os.environ.get("VERTEX_PROJECT", "").strip())
    return bool(os.environ.get(cfg["key_env"])) and bool(cfg["base_url"])


def _resolve() -> tuple[str, dict]:
    forced = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if forced == "vertex":
        return "vertex", _prepare_vertex()
    if forced in _PROVIDERS:
        return forced, _PROVIDERS[forced]
    # Auto-pick in Aditya's priority order: KCL ARC first, then GitHub
    # Models, then the Gemini routes. RADAR is not auto-picked any more;
    # LLM_PROVIDER=radar still reaches it.
    for name in ("arc", "github", "gemini", "vertex"):
        cfg = _prepare_vertex() if name == "vertex" else _PROVIDERS[name]
        if _usable(name, cfg):
            return name, cfg
    return "github", _GITHUB


PROVIDER, _CFG = _resolve()
MODEL = os.environ.get("LLM_MODEL", "").strip() or _CFG["model"]


def _client_kwargs(http_client=None) -> dict:
    if PROVIDER == "vertex":
        key = _vertex_token()
        if not key:
            raise SystemExit(
                "No Vertex access token.\n"
                "Run:  gcloud auth login   then   gcloud auth print-access-token\n"
                "or set VERTEX_ACCESS_TOKEN in .env. Tokens expire after ~1 hour."
            )
    else:
        key = os.environ.get(_CFG["key_env"])
        if not key:
            raise SystemExit(
                f"No API key for provider '{PROVIDER}'.\n"
                f"Set {_CFG['key_env']} in the .env file at the repo root."
            )
    if not _CFG["base_url"]:
        raise SystemExit(
            f"No base_url for provider '{PROVIDER}'.\n"
            "RADAR needs RADAR_OPEN_MODEL_BASE_URL; Vertex needs VERTEX_PROJECT."
        )
    kwargs = {"base_url": _CFG["base_url"], "api_key": key}
    if http_client is not None:      # so a caller can watch the raw HTTP
        kwargs["http_client"] = http_client
    return kwargs


def build_client(http_client=None) -> OpenAI:
    """Sync client. Use this unless you specifically need async."""
    return OpenAI(**_client_kwargs(http_client))


def build_async_client(http_client=None) -> AsyncOpenAI:
    """Async client — the real-world agent shape, wanted once loops appear."""
    return AsyncOpenAI(**_client_kwargs(http_client))


def ask(client: OpenAI, messages: list, show_thinking: bool = False, **kw) -> str:
    """Send messages, return the reply text. Survives rate limits and filters.

    show_thinking=False (default): strip any <think>...</think> block.
    show_thinking=True:            keep it, so you can see the raw reasoning.
    """
    kw.setdefault("temperature", 0)
    for attempt in range(4):
        try:
            resp = client.chat.completions.create(model=MODEL, messages=messages, **kw)
            content = resp.choices[0].message.content
            # Thinking models can spend the whole max_tokens budget on hidden
            # reasoning and return no text. Never hand back None.
            if content is None:
                return "<<no text — model spent the token budget on reasoning; raise max_tokens>>"
            if show_thinking:
                return content.strip()
            return _THINK_RE.sub("", content).strip()
        except (RateLimitError, InternalServerError,
                APITimeoutError, APIConnectionError) as e:
            # Transient: free-tier rate limit (429), server busy, network blip.
            if attempt == 3:
                return f"<<temporary provider error ({type(e).__name__}); wait and re-run>>"
            time.sleep(5 * (attempt + 1))
        except BadRequestError:
            # Providers filter obvious "ignore your instructions" attacks (400).
            return "<<blocked by the provider's content filter>>"
    return "<<unreachable>>"


def describe() -> str:
    """One line naming the active provider and model — printed by every script."""
    return f"provider={PROVIDER}  model={MODEL}  base_url={_CFG['base_url']}"
