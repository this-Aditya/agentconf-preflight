# agentconf-preflight

Pre-conference groundwork for LFX AGNTCon + MCPCon Europe 2026: agent loops and harness engineering, stateless MCP servers and extensions,
agent identity via OAuth 2.1 and token exchange, A2A multi-agent orchestration, and
OpenTelemetry-backed evals.

Modules in dependency order — nothing is explained with a word an earlier module
hasn't introduced.

## Modules

| Folder | Subject |
|--------|---------|
| `setup/` | Provider client, model catalogue, rate limits ✅ |
| `agent_loop/` | The agent loop, written by hand |
| `mcp_foundations/` | MCP: hosts, clients, servers |
| `mcp_server/` | The spec, then your own server |
| `stateless_mcp/` | Unlearning the `initialize` handshake |
| `mcp_extensions/` | Tasks, multi-round-trip requests, Apps |
| `harness_and_skills/` | Harnesses, Skills, context engineering |
| `agent_identity/` | OAuth 2.1, PKCE, token exchange, audience |
| `multi_agent/` | A2A and orchestration patterns |
| `observability_evals/` | OpenTelemetry GenAI traces, golden sets |
| `security_platform/` | Prompt injection, gateways, control planes |

Folders are created as each module is reached, not up front.

## Layout

```
shared/llm.py     the only file that names a provider
setup/            one folder per module
pyproject.toml    one uv project — one interpreter for PyCharm
```

Every provider here speaks the OpenAI API shape, so switching is `base_url` +
`api_key` + model name and nothing else. Modules import
`from shared.llm import build_client, ask, MODEL, PROVIDER` and never learn which
provider they are on — which matters, because MCP splits the same way: a server has
no idea which model is on the other end.

| Provider | State |
|---|---|
| `arc` — KCL ARC-AI | **primary.** Tool calling confirmed on lite/nano/apex.  |
| `github` — GitHub Models | fallback; currently `410`, mid-retirement |
| `gemini` — AI Studio key | fallback; needs a funded AI Studio prepay balance |
| `vertex` — Gemini on Vertex AI | fallback; OAuth token, spends Google Cloud credits |
| `radar` — KCL RADAR | not auto-picked; reachable with `LLM_PROVIDER=radar` |

## Running it

```bash
cp .env.example .env                              # then add your keys
uv sync
uv run python setup/check_env.py            # what will actually run
uv run python setup/hello.py                # one completion
```

PyCharm: open this folder, set the interpreter to `.venv/bin/python`
(Settings → Project → Python Interpreter → Add → Existing), and mark the project root
as a source root so `from shared.llm import ...` resolves.
