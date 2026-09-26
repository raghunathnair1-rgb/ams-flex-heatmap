"""Standalone MCP server exposing real AMS flight-price search as a tool.

Runs over stdio, so any MCP client (Claude Desktop, other agents) can use it
directly. Shares the exact same Amadeus-backed logic as the web app
(api/flights.py, api/amadeus_client.py) — one implementation, two front doors.

Run:
    python mcp-server/server.py

Register in an MCP client (e.g. Claude Desktop config):
    {
      "mcpServers": {
        "ams-flights": {
          "command": "python",
          "args": ["/absolute/path/to/mcp-server/server.py"],
          "env": {
            "AMADEUS_CLIENT_ID": "...",
            "AMADEUS_CLIENT_SECRET": "..."
          }
        }
      }
    }
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

from mcp.server.fastmcp import FastMCP  # noqa: E402

from api.flights import search_flights  # noqa: E402

mcp = FastMCP("ams-flex-flight-search")


@mcp.tool()
def search_flights_ams(destination: str, start_date: str, end_date: str) -> dict:
    """Search real flex-date flight prices from Amsterdam Schiphol (AMS) to a
    destination over a date range (ISO dates, e.g. 2026-04-01).

    Returns day-by-day prices, the cheapest day (enriched with airline/stops/
    duration), and which data source produced the result (real Amadeus data
    vs. a clearly-labeled mock fallback if no API credentials are configured).
    This is the ONLY tool this server exposes — no code execution, no general
    web search, nothing else.
    """
    return search_flights(destination=destination, start_date=start_date, end_date=end_date, origin="AMS")


if __name__ == "__main__":
    mcp.run(transport="stdio")
