"""
trace.py — print what the loop is doing, in both directions.

The loop is invisible by default: you see the final answer and nothing about how
it got there. These three helpers make each step visible, which is the whole
point of watching the transcript grow.

Import and call them from your loop:

    from b_agent_loop.trace import show_reply, show_tool, show_transcript
"""

import json

# --- how much of a tool result to show before cutting it off ---
RESULT_CHARS = 300


def show_reply(turn: int, message) -> None:
    """Print what came BACK from the model on this turn."""
    if message.tool_calls:
        print(f"\n\033[1m── TURN {turn}  ← model asked for {len(message.tool_calls)} tool(s)\033[0m")
        for tc in message.tool_calls:
            args = tc.function.arguments
            print(f"   ask  {tc.function.name}({args})")
            print(f"        id={tc.id}")
    else:
        print(f"\n\033[1m── TURN {turn}  ← model answered with text\033[0m")
        print(f"   {len((message.content or '')):,} chars — loop will now exit")

    # arc:lite exposes its deliberation; most providers do not.
    reasoning = getattr(message, "reasoning_content", None)
    if reasoning:
        print(f"   \033[2mthinking: {' '.join(reasoning.split())[:160]}\033[0m")


def show_tool(name: str, args: dict, result: str) -> None:
    """Print what YOU ran, and what you are sending back."""
    shown = " ".join(result.split())[:RESULT_CHARS]
    more = f"  … +{len(result) - RESULT_CHARS} chars" if len(result) > RESULT_CHARS else ""
    flag = "  \033[31m[ERROR]\033[0m" if result.startswith("ERROR:") else ""
    print(f"   ran  {name}({json.dumps(args)}){flag}")
    print(f"        -> {shown}{more}")


def show_transcript(messages: list) -> None:
    """Print the transcript as a numbered list of roles — the thing that grows."""
    print(f"\n\033[1m── TRANSCRIPT: {len(messages)} messages, all resent every turn\033[0m")
    for i, m in enumerate(messages):
        role = m.get("role", "?")
        detail = ""
        if m.get("tool_calls"):
            names = ", ".join(tc["function"]["name"] for tc in m["tool_calls"])
            detail = f"  tool_calls x{len(m['tool_calls'])}  ({names})"
        elif m.get("tool_call_id"):
            detail = f"  tool_call_id=…{m['tool_call_id'][-8:]}"
        elif m.get("content"):
            detail = f"  {len(m['content']):,} chars"
        print(f"   [{i}] {role:<9}{detail}")
