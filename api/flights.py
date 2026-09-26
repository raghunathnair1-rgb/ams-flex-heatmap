"""Flight-price tool: real Amadeus data when credentials are configured
(see amadeus_client.py), otherwise a deterministic mock so the app still
runs without an API key. Every result carries a "source" field so the UI/user
always knows which one they're looking at — never silently fake."""
from __future__ import annotations

import hashlib
import os
from datetime import date, timedelta

# Rough base fares (EUR, one-way) from Amsterdam (AMS) used to seed the mock.
BASE_FARES = {
    "barcelona": 65, "bcn": 65,
    "lisbon": 90, "lis": 90,
    "rome": 85, "fco": 85,
    "athens": 110, "ath": 110,
    "new york": 320, "jfk": 320, "nyc": 320,
    "bangkok": 480, "bkk": 480,
    "tokyo": 620, "nrt": 620, "hnd": 620,
    "cape town": 550, "cpt": 550,
    "dubai": 340, "dxb": 340,
    "reykjavik": 140, "kef": 140,
    "istanbul": 130, "ist": 130,
    "bali": 590, "dps": 590,
    "singapore": 560, "sin": 560,
}

AIRLINES = ["KLM", "Transavia", "Air France", "TAP Air Portugal", "Turkish Airlines"]


def _base_fare(destination: str) -> float:
    key = destination.strip().lower()
    for name, fare in BASE_FARES.items():
        if name in key:
            return fare
    # Unknown destination: derive a stable pseudo-base fare from the name.
    h = int(hashlib.sha256(key.encode()).hexdigest(), 16)
    return 80 + (h % 500)


def _price_for_date(destination: str, day: date) -> dict:
    base = _base_fare(destination)
    h = int(hashlib.sha256(f"{destination.lower()}|{day.isoformat()}".encode()).hexdigest(), 16)

    # Weekend departures run pricier; Tue/Wed are the classic cheap days.
    weekday_factor = [1.0, 0.9, 0.85, 0.95, 1.15, 1.35, 1.25][day.weekday()]
    # Deterministic "noise" in +/-18% band, seeded per date+destination.
    noise = 0.82 + (h % 1000) / 1000 * 0.36
    # Summer (Jun-Aug) and Christmas week surcharge, like real seasonality.
    season_factor = 1.25 if day.month in (6, 7, 8) else (1.3 if day.month == 12 and day.day >= 18 else 1.0)

    price = round(base * weekday_factor * noise * season_factor, 2)
    airline = AIRLINES[h % len(AIRLINES)]
    stops = 0 if (h // 7) % 3 == 0 else 1
    duration_min = 90 + (h % 600) if base < 200 else 360 + (h % 900)

    return {
        "date": day.isoformat(),
        "price": price,
        "currency": "EUR",
        "airline": airline,
        "stops": stops,
        "duration_min": duration_min,
    }


def search_flights(destination: str, start_date: str, end_date: str, origin: str = "AMS") -> dict:
    """Tool: real Amadeus fares if AMADEUS_CLIENT_ID/SECRET are configured,
    else a deterministic mock (clearly labeled) so the app still runs without
    credentials."""
    if os.environ.get("AMADEUS_CLIENT_ID") and os.environ.get("AMADEUS_CLIENT_SECRET"):
        from .amadeus_client import search_flights_real

        try:
            return search_flights_real(destination, start_date, end_date, origin)
        except Exception as exc:  # noqa: BLE001 - fall back to mock, but say why
            import traceback

            traceback.print_exc()  # surfaces in Vercel function logs for debugging
            result = _search_flights_mock(destination, start_date, end_date, origin)
            result["source"] = f"mock (Amadeus error: {type(exc).__name__}: {exc})"
            return result

    result = _search_flights_mock(destination, start_date, end_date, origin)
    result["source"] = "mock (no AMADEUS_CLIENT_ID/SECRET configured)"
    return result


def _search_flights_mock(destination: str, start_date: str, end_date: str, origin: str = "AMS") -> dict:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    if end < start:
        start, end = end, start
    if (end - start).days > 60:
        end = start + timedelta(days=60)  # cap tool-call cost / response size

    days = []
    cur = start
    while cur <= end:
        days.append(_price_for_date(destination, cur))
        cur += timedelta(days=1)

    cheapest = min(days, key=lambda d: d["price"])
    return {
        "origin": origin.upper(),
        "destination": destination,
        "days": days,
        "cheapest": cheapest,
    }
