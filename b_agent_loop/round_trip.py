import json

from shared.llm import build_client, MODEL

client = build_client()

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_horoscope",
            "description": "Get a daily horoscope",
            "parameters": {
                "type": "object",
                "properties": {
                    "sign": {
                        "type": "string",
                        "description": "An Astrological sign, like aries"
                    }
                },
                "required": ["sign"]
            }
        }
    }
]


def get_horoscope(sign: str) -> str:
    return f"Your horoscope for {sign} is: Today is a great day to embrace new opportunities and trust your instincts."

messages = [
    {
        "role": "user",
        "content": "Good Morning, please tell my today's horoscope for aries in complete depth"
    }
]

response = client.chat.completions.create(tools = tools, messages = messages, model = MODEL)

response_message = response.choices[0].message

print("DEBUG -- Model Dump: ", response_message.model_dump(exclude_none=True), "\n\n")

messages.append(response_message.model_dump(exclude_none=True))

for tool_call in response_message.tool_calls:
    if tool_call.function.name == "get_horoscope":
        args = json.loads(tool_call.function.arguments)

        horoscope = get_horoscope(**args)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": horoscope
        })

final_response = client.chat.completions.create(messages = messages, model = MODEL, tools = tools)

print("Final Answer is: \n", final_response.choices[0].message.content)
















