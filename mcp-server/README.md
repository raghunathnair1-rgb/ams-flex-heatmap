# AMS Flight Search — MCP Server

Exposes the exact same real-data flight search (`api/flights.py` →
`api/amadeus_client.py`) as a standard MCP tool over stdio, so any MCP client
(Claude Desktop, other agents) can call it directly — not just the web app.

**One tool only**: `search_flights_ams(destination, start_date, end_date)`.
No code execution, no web browsing, no other tool is registered here.

## Run standalone

```bash
cd ..
python -m venv .venv && source .venv/bin/activate
pip install -r mcp-server/requirements.txt
cp .env.example .env   # fill in AMADEUS_CLIENT_ID / AMADEUS_CLIENT_SECRET
python mcp-server/server.py
```

## Use from Claude Desktop

Add to Claude Desktop's MCP config (Settings → Developer → Edit Config):

```json
{
  "mcpServers": {
    "ams-flights": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/mcp-server/server.py"],
      "env": {
        "AMADEUS_CLIENT_ID": "your-client-id",
        "AMADEUS_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

Restart Claude Desktop, then ask it something like "use ams-flights to find
the cheapest week to fly AMS → Lisbon in November."

Amadeus for Developers Self-Service was permanently shut down in July 2026,
so those env vars are no longer usable against any real provider — without
them (the current default), the tool runs on clearly labeled mock data
(`"source": "mock (no AMADEUS_CLIENT_ID/SECRET configured)"`).
