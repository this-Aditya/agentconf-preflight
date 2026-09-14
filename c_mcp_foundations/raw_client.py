"""Talk to server.py by hand: a subprocess and JSON written by hand, no MCP client library.

Run from the repo root:  uv run python -m c_mcp_foundations.raw_client
"""

import json
import subprocess
import sys
from pathlib import Path

SERVER = Path(__file__).resolve().parent / "server.py"

# Goes inside `params` on every request. Without it the server refuses to answer.
META = {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientCapabilities": {},
    "io.modelcontextprotocol/clientInfo": {"name": "raw_client", "version": "0"},
}


def start_server() -> subprocess.Popen:
    # stdio transport: we start the server ourselves and talk through its stdin/stdout.
    # stderr is hidden so the server's own logs don't mix into our printout.
    return subprocess.Popen(
        [sys.executable, str(SERVER)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )


def send(server: subprocess.Popen, message: dict) -> dict:
    """Write one request as one line, read one line back as the reply."""
    line = json.dumps(message)
    print("SENT:\n" + json.dumps(message, indent=2))
    server.stdin.write(line + "\n")      # the newline marks the end of the message
    server.stdin.flush()                 # push it now, don't wait in a buffer

    reply = json.loads(server.stdout.readline())
    print("RECEIVED:\n" + json.dumps(reply, indent=2) + "\n")
    return reply


def request(id: int, method: str, **params) -> dict:
    """Build a request: jsonrpc, id, method, and params (inputs + _meta)."""
    return {"jsonrpc": "2.0", "id": id, "method": method, "params": {**params, "_meta": META}}


def main():
    server = start_server()

    print("=" * 20, "the normal calls", "=" * 20, "\n")

    # "Who are you, what can you do?"
    send(server, request(1, "server/discover"))

    # "What tools do you have?" (their names, descriptions and schemas)
    send(server, request(2, "tools/list"))

    # "Run list_dir with path='c_mcp_foundations'."
    send(server, request(3, "tools/call", name="list_dir", arguments={"path": "c_mcp_foundations"}))

    # "Give me the resource at this URI."
    send(server, request(4, "resources/read", uri="repo://readme"))

    print("=" * 20, "breaking it on purpose", "=" * 20, "\n")

    # 1. No _meta at all (built by hand, not with request()).
    send(server, {"jsonrpc": "2.0", "id": 5, "method": "tools/list"})

    # 2. A protocol version the server doesn't speak.
    bad_version = request(6, "tools/list")
    bad_version["params"]["_meta"] = {**META, "io.modelcontextprotocol/protocolVersion": "1999-01-01"}
    send(server, bad_version)

    # 3. A tool that doesn't exist.
    send(server, request(7, "tools/call", name="no_such_tool", arguments={}))

    # 4. A tool that exists but raises an exception while running.
    send(server, request(8, "tools/call", name="always_fails", arguments={}))

    server.stdin.close()   # closing stdin tells the server we're done; it exits
    server.wait(timeout=5)


if __name__ == "__main__":
    main()
