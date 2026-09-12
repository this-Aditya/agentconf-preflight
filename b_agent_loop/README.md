




----
## My Notes 

**Response structure:**

For Response API:

```json
response
└── output ················· a LIST of different kinds of thing
    ├── {type: "reasoning",     ...}
    ├── {type: "function_call",  name, arguments, call_id}
    └── {type: "message",        content}
```

For Chat Completions:
```json
response
└── choices[0]
    ├── finish_reason ········ "tool_calls" | "stop"
    └── message
        ├── content ·········· None when tools were requested
        └── tool_calls ······· a LIST, or None
            └── [0]
                ├── id ······· the join key
                └── function
                    ├── name
                    └── arguments ··· JSON *string*
```

And the tool id has to match the tool answer:

```
message.tool_calls[0].id   ──copy──▶   {"role":"tool", "tool_call_id": <same>, ...}
```

### Entities:
```
┌───────────┬────────────────────────┬────────────────────────────────────────────────────┐
│   role    │          who           │                   what it holds                    │
├───────────┼────────────────────────┼────────────────────────────────────────────────────┤
│ system    │ you, setting the rules │ standing instructions: "answer only in JSON"       │
├───────────┼────────────────────────┼────────────────────────────────────────────────────┤
│ user      │ you, asking            │ the question                                       │
├───────────┼────────────────────────┼────────────────────────────────────────────────────┤
│ assistant │ the model              │ what the model said — text, or a request for tools │
├───────────┼────────────────────────┼────────────────────────────────────────────────────┤
│ tool      │ your code              │ the return value of a function you ran             │
└───────────┴────────────────────────┴────────────────────────────────────────────────────┘
```