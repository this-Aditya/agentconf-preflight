"""An MCP server with one of each: tools, a resource, and a prompt.

Run it in the Inspector:  uv run mcp dev c_mcp_foundations/server.py
"""

from pathlib import Path

from mcp.server.mcpserver import MCPServer

ROOT = Path(__file__).resolve().parent.parent   # the repo root
MAX_BYTES = 18_000                               # ~2k tokens of file content
MAX_ENTRIES = 200                                # directory listing cap

# The server's name and version come back in every response, in `_meta.serverInfo`.
mcp = MCPServer("agentconf-files", version="0.1.0")


# --- helpers (not exposed over MCP) -------------------------------------------
# Copied from b_agent_loop/file_info.py. Importing that file would run its agent
# loop, so the functions are repeated here instead.

def _safe(path: str) -> Path | str:
    """Resolve `path` inside ROOT. Returns a Path, or an error string."""
    try:
        target = (ROOT / path).resolve()
    except (OSError, ValueError) as e:
        return f"ERROR: bad path {path!r} ({e.__class__.__name__})"
    if target != ROOT and ROOT not in target.parents:
        return (f"ERROR: {path!r} resolves outside the project "
                f"(to {target}). Only paths inside the project are allowed.")
    return target


# --- tools: the MODEL decides when to call these -------------------------------
# `@mcp.tool()` takes no name: the function name becomes the tool name.
# The docstring becomes `description`, the type hints become `inputSchema`.
# In b_agent_loop you wrote that JSON by hand in TOOLS; here it is generated.

@mcp.tool()
def list_dir(path: str = ".") -> str:
    """List the entries in a directory inside the project."""
    target = _safe(path)
    if isinstance(target, str):
        return target
    if not target.exists():
        return f"ERROR: no such directory {path!r}. Try list_dir('.') to see what exists."
    if not target.is_dir():
        return f"ERROR: {path!r} is a file, not a directory. Use read_file for it."

    entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name))
    lines = [f"{p.name}/" if p.is_dir() else p.name for p in entries[:MAX_ENTRIES]]
    if not lines:
        return f"{path} is empty."
    out = "\n".join(lines)
    if len(entries) > MAX_ENTRIES:
        out += f"\n... {len(entries) - MAX_ENTRIES} more entries not shown"
    return out


@mcp.tool()
def read_file(path: str) -> str:
    """Read a text file inside the project."""
    target = _safe(path)
    if isinstance(target, str):
        return target
    if not target.exists():
        return f"ERROR: no such file {path!r}. Use list_dir to find the right name."
    if target.is_dir():
        return f"ERROR: {path!r} is a directory, not a file. Use list_dir for it."

    try:
        data = target.read_bytes()
    except OSError as e:
        return f"ERROR: could not read {path!r} ({e.__class__.__name__})"

    truncated = len(data) > MAX_BYTES
    try:
        text = data[:MAX_BYTES].decode("utf-8")
    except UnicodeDecodeError:
        return f"ERROR: {path!r} is not a text file ({len(data)} bytes of binary)."

    if truncated:
        text += f"\n\n... truncated: showed {MAX_BYTES} of {len(data)} bytes"
    return text


@mcp.tool()
def always_fails() -> str:
    """A tool that raises on purpose. Used by raw_client.py to see what a crash looks like."""
    raise RuntimeError("this tool always fails")


# --- resource: the APP decides when to fetch this ------------------------------
# A resource is found by its URI, not by a name. `repo://` is made up; any
# scheme works. The model never sees this as something it can call.
# Fetched with `resources/read` and {"uri": "repo://readme"}.

@mcp.resource("repo://readme", mime_type="text/markdown")
def readme() -> str:
    """The project README."""
    return (ROOT / "README.md").read_text(encoding="utf-8")


# --- prompt: the USER picks this, e.g. from a menu -----------------------------
# The function returns the message that will be sent to the model. Returning
# a plain string gives one message with role "user".
# The `module` parameter becomes an argument the user fills in.
# Fetched with `prompts/get` and {"name": "summarise_module", "arguments": {...}}.

@mcp.prompt()
def summarise_module(module: str) -> str:
    """Ask for a short summary of one module in this repo."""
    return (
        f"Summarise the `{module}` module of this repository in a few sentences. "
        f"Use list_dir and read_file to look at its files first. "
        f"Say what it teaches and which file to open first."
    )


if __name__ == "__main__":
    # stdio: the Inspector (or any host) starts this file as a subprocess and
    # sends one JSON message per line on stdin; replies come out on stdout.
    mcp.run(transport="stdio")
