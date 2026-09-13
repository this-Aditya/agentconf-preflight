import json

from shared.llm import build_client, MODEL

model = build_client()

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent   # the repo root
MAX_BYTES = 18_000                               # ~2k tokens of file content
MAX_ENTRIES = 200                               # directory listing cap


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


# The JSON the model reads. Description and parameter descriptions are the only
# things it has to go on when deciding what to ask for — they are prompt text.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List the files and directories at a path inside the project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path relative to the project root, e.g. '.' or 'a_setup'",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a text file inside the project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path relative to the project root, e.g. 'README.md'",
                    }
                },
                "required": ["path"],
            },
        },
    },
]

# name -> function, so a loop can dispatch without a chain of ifs
DISPATCH = {"list_dir": list_dir, "read_file": read_file}

messages = [
    {
        "role": "user",
        "content": "Hi, in the current repo please summarize the contents of the readme file in short"
    }
]

response = model.chat.completions.create(tools = TOOLS, messages = messages, model = MODEL)

response_message = response.choices[0].message
messages.append(response_message.model_dump(exclude_none=True))

while response_message.tool_calls:
    for tool_call in response_message.tool_calls:
        args = json.loads(tool_call.function.arguments)
        result = DISPATCH[tool_call.function.name](**args)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        })
    response = model.chat.completions.create(messages = messages, model = MODEL, tools = TOOLS)
    response_message = response.choices[0].message
    messages.append(response_message.model_dump(exclude_none=True))

print("Final Answer is: \n", response_message.content)


def main():
    pass

if __name__ == "__main__":
    main()

