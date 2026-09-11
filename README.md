# agentconf

Working repo for the **Ten Days to AGNTCon** study plan — AGNTCon + MCPCon Europe,
17–18 September 2026, Amsterdam.

The plan itself:
<https://claude.ai/code/artifact/df474e66-0fa7-478a-b878-0d0d9cecbe57>

## Shape of this repo

One uv project, one virtualenv, one interpreter for PyCharm to point at. Each day
of the plan is a folder added **when you reach it**, not all up front:

```
agentconf/
├── pyproject.toml          # single project; per-day deps are optional groups
├── .env                    # gitignored; your keys
├── shared/llm.py           # the provider switch — every day imports from here
└── day00_setup/            # <- you are here
```

## Providers

`shared/llm.py` builds an OpenAI-SDK client for whichever provider you have, because
they all speak the OpenAI API shape. Switching is `base_url` + `api_key` + model name;
no lesson code changes. Auto-picked in this order, or forced with `LLM_PROVIDER`:

`gemini` → `vertex` → `radar` → `arc` → `github`

Keys go in `.env` (copy `.env.example`); the variable names match
`../agent-sandbox/4.tool-calling/.env` so they paste straight across.

## Running anything

```bash
uv sync                                          # first time only
uv run python day00_setup/check_env.py           # what will actually run
uv run python day00_setup/hello.py               # one completion
```

In PyCharm: open this folder, then set the interpreter to `.venv/bin/python`
(Settings → Project → Python Interpreter → Add → Existing → `.venv/bin/python`).
Mark the project root as a source root so `from shared.llm import ...` resolves.

## Days

| Day | Folder | Hours | Subject |
|-----|--------|-------|---------|
| 00 | `day00_setup/` | 45 min | Setup on your own stack |
| 01 | — | 4 h 30 | Build one agent, by hand |
| 02 | — | 4 h 30 | The MCP course, at its real speed |
| 03 | — | 5 h | Read the spec, then build a server |
| 04 | — | 4 h 40 | Unlearn the handshake (stateless MCP) |
| 05 | — | 4 h | The parts of MCP the talks are about |
| 06 | — | 4 h 30 | Harnesses, Skills, memory and context |
| 07 | — | 4 h 40 | Identity — the hardest day |
| 08 | — | 3 h 30 | More than one agent (A2A) |
| 09 | — | 5 h | Proving it works (traces, evals) |
| 10 | — | 4 h 10 | Security, platform, and your schedule |

45¼ hours total. Folders get created one day at a time.
