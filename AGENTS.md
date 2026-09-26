# Agent Engineering Notes

Standing context for this project's agent, following the harness / loop /
skills / graph split from agent-engineering fundamentals. Each section names
exactly where that concept lives in the code — this file is a map, not a
duplicate of the implementation.

## Harness engineering

The harness is everything around the model: prompt, context, tools, loop.

| Piece    | File                     |
|----------|--------------------------|
| Prompt   | `SYSTEM_ROLE` in `api/agent.py` — one short, scope-locked system role |
| Context  | `api/index.py` `chat()` — sanitizes client history (role allowlist, length/turn caps) before it reaches the model |
| Tools    | `skills/search_flights.skill.md` (spec) → `api/flights.py` (implementation) → registered in `TOOLS` in `api/agent.py` |
| Loop     | `run_agent()` in `api/agent.py` |

Model calls go to Azure AI Foundry (`api/agent.py: _client()`), configured
entirely from environment variables (`.env` locally, Vercel project env vars
in production) — never hardcoded.

## Loop engineering

`run_agent()` in `api/agent.py` runs the classic bounded loop:

```
user message → guardrail check → model call → tool call(s)? → tool result → model call → ... → final answer
```

Bounds enforced in code (`MAX_LOOP_ITERATIONS`, `MAX_TOOL_CALLS`,
`MAX_RETRIES` at the top of `api/agent.py`):

- **loop cap**: 5 model turns per request — if the model hasn't produced a
  final answer by then, the loop forces one plain-text summary and stops.
- **tool-call cap**: 3 tool calls per request.
- **retry cap**: 3 attempts per failing tool call before it reports failure
  instead of retrying forever.

## Skills

One skill is registered, deliberately: `search_flights`. Its spec lives in
`skills/search_flights.skill.md` (write once, referenced by both the web
agent and the MCP server, not redefined twice). No other skill exists in
this app — that's the point of the scope guardrails in `api/guardrails.py`:
a single, auditable tool surface.

## Graph engineering

Agents as nodes and edges, not a single line. Today's graph is intentionally
small — one agent node, one tool node — matching the scope lockdown:

```
React UI  →  FastAPI (api/index.py)  →  Agent loop (api/agent.py)  →  Tool node: search_flights
                                                                          ├─ direct call (web app, api/flights.py)
                                                                          └─ MCP call  (mcp-server/server.py, any MCP client)
```

Two edges lead out of the same tool node — the web app calls
`api/flights.py` in-process for serverless reliability, and the standalone
MCP server (`mcp-server/`) exposes the identical logic over stdio to any
other MCP client (Claude Desktop, another agent). One skill, two front doors,
same guardrails on both.

**Scaling this graph**, if ever needed (main-agent → sub-agents, Hadoop-style
fan-out/collect): would mean adding new tool nodes behind the same allowlist
pattern in `api/guardrails.py` (`ALLOWED_TOOLS`), each with its own skill spec
in `skills/`, and a router step in `run_agent()` before the loop. Not built
now — the current one-skill graph is deliberate, not a placeholder.
