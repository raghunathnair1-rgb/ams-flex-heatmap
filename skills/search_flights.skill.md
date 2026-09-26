---
name: search_flights
description: Real/mock flex-date flight prices from Amsterdam Schiphol (AMS) to a destination over a date range. Use whenever the user asks about flight prices, cheapest days to fly, or flexible travel dates out of AMS.
implemented_in: api/flights.py (search_flights), wrapped as an MCP tool in mcp-server/server.py (search_flights_ams)
---

# Skill: search_flights

Write-once, call-again tool definition — this file is the single source of
truth for what the skill does and how it's guarded. The agent loop
(`api/agent.py`) and the MCP server (`mcp-server/server.py`) both point back
here rather than each carrying their own description.

## When to use

- User names a destination and is flexible (or open) on travel dates.
- User asks "cheapest day/week to fly to X", "flex dates to X", or similar.
- Never for anything outside AMS-origin flight search — see guardrails below.

## Inputs

| param        | type | required | notes                                  |
|--------------|------|----------|-----------------------------------------|
| destination  | str  | yes      | city or airport name/IATA code          |
| start_date   | str  | yes      | ISO date, e.g. 2026-04-01               |
| end_date     | str  | yes      | ISO date; range capped at 60 days       |
| origin       | str  | no       | defaults to "AMS"                       |

## Output shape

```json
{
  "origin": "AMS",
  "destination": "Lisbon",
  "days": [{"date": "...", "price": 0.0, "currency": "EUR", "airline": "...", "stops": 0, "duration_min": 0}],
  "cheapest": { "...": "same shape as one day entry" },
  "source": "mock (...)" | "Amadeus (test|production environment)"
}
```

`source` must always be present and truthful — mock data is never presented
as real. This is what the frontend's data-source badge reads.

## Data source

Real data (Amadeus Self-Service) was planned but the provider **permanently
shut down its Self-Service portal in July 2026** — see `api/amadeus_client.py`
for the (now-defunct) reference wiring and `README.md` for the incident
writeup. Current default: deterministic mock, clearly labeled.

## Guardrails applied around this skill (not inside it)

Enforced in `api/guardrails.py` and `api/agent.py`, one layer above the skill
itself, so the skill function stays simple and these rules can't be bypassed
by changing the skill's own code:

- **Tool allowlist**: this is the *only* tool the agent may ever call.
- **Loop cap**: max 5 model turns per request.
- **Call cap**: max 3 invocations of this skill per request.
- **Retry cap**: a failing call retries at most 3 times, then reports failure
  in the `source`/error field rather than crashing the turn.
- **Input filter**: off-topic requests never reach this skill or the model.
