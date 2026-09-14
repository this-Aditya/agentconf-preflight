"""The agent loop from b_agent_loop/file_info.py, with the tools served by MCP.

Before: list_dir / read_file were Python functions in the same file, and TOOLS was
JSON written by hand.
Now: they live in server.py, a separate process. The loop asks the server for its
tools (tools/list) and asks it to run them (tools/call).

Run from the repo root:  uv run python -m c_mcp_foundations.mcp_agent
"""

import asyncio
import json
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

from shared.llm import build_async_client, MODEL, describe

SERVER = Path(__file__).resolve().parent / "server.py"

QUESTION = "Hi, in the current repo please summarize the contents of the readme file in short"


def to_openai_tool(tool) -> dict:
    """An MCP tool (from tools/list) -> the tool format the model API expects.

    Compare with TOOLS in file_info.py: same three things (name, description,
    parameters), but here nobody wrote them; the server generated them.
    """
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.input_schema,
        },
    }


def result_text(result) -> str:
    """Join the text blocks of a tools/call result. This is what the model reads."""
    text = "\n".join(block.text for block in result.content if block.type == "text")
    # A failed tool is not an exception: it's a normal result with is_error=True.
    # We pass the text to the model anyway, so it can see what went wrong.
    return f"ERROR: {text}" if result.is_error else text


async def main():
    print(describe())
    model = build_async_client()

    # Tell the client how to start the server. It launches `python server.py`
    # as a subprocess and talks over stdio, just like raw_client.py did by hand.
    server = StdioServerParameters(command=sys.executable, args=[str(SERVER)])

    async with Client(server) as mcp:
        # 1. Ask the server what tools it has.   (tools/list)
        listed = await mcp.list_tools()
        tools = [to_openai_tool(t) for t in listed.tools]
        print("tools from the server:", [t["function"]["name"] for t in tools])

        messages = [{"role": "user", "content": QUESTION}]

        # 2. The same loop as file_info.py.
        response = await model.chat.completions.create(model=MODEL, messages=messages, tools=tools)
        response_message = response.choices[0].message
        messages.append(response_message.model_dump(exclude_none=True))

        while response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                print(f"model called {name}({args})")

                # The only real change: instead of DISPATCH[name](**args),
                # ask the server to run it.   (tools/call)
                result = await mcp.call_tool(name, args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_text(result),
                })

            response = await model.chat.completions.create(model=MODEL, messages=messages, tools=tools)
            response_message = response.choices[0].message
            messages.append(response_message.model_dump(exclude_none=True))

    print("\nFinal answer:\n", response_message.content)


if __name__ == "__main__":
    asyncio.run(main())
