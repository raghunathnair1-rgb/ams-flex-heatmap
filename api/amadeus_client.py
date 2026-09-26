"""Real flight data via Amadeus for Developers (Self-Service).

Two calls per query:
  1. Flight Cheapest Date Search -> real price per day across the date range
     (this is the API purpose-built for flexible-date search).
  2. Flight Offers Search, once, only for the cheapest day -> real airline,
     stop count, and duration to enrich that one day.

Docs: https://developers.amadeus.com/self-service/category/flights
Note: AMADEUS_ENV=test (default) hits the free test environment, which
serves real airline-sourced fares but from a cached/aggregated test dataset,
not a live production feed. Set AMADEUS_ENV=production with a production
key for fully live pricing.
"""
from __future__ import annotations

import os
import time

import requests

_token_cache: dict = {"access_token": None, "expires_at": 0}


def _request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
    """Serverless sandboxes occasionally throw a transient OSError (e.g.
    'Device or resource busy') on the first socket/DNS call in a cold
    instance; retry a couple of times before giving up."""
    last_exc = None
    for attempt in range(3):
        try:
            return requests.request(method, url, **kwargs)
        except (OSError, requests.exceptions.ConnectionError) as exc:
            last_exc = exc
            time.sleep(0.3 * (attempt + 1))
    raise last_exc


def _base_url() -> str:
    env = os.environ.get("AMADEUS_ENV", "test").lower()
    return "https://api.amadeus.com" if env == "production" else "https://test.api.amadeus.com"


def _get_token() -> str:
    now = time.time()
    if _token_cache["access_token"] and now < _token_cache["expires_at"] - 30:
        return _token_cache["access_token"]

    client_id = os.environ["AMADEUS_CLIENT_ID"]
    client_secret = os.environ["AMADEUS_CLIENT_SECRET"]

    resp = _request_with_retry(
        "POST",
        f"{_base_url()}/v1/security/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 1800)
    return _token_cache["access_token"]


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_get_token()}"}


def resolve_iata(destination: str) -> str:
    """City/airport name -> IATA city code, via Amadeus Airport & City Search."""
    # Already looks like an IATA code (e.g. "BCN", "LIS").
    if len(destination.strip()) == 3 and destination.strip().isalpha():
        return destination.strip().upper()

    resp = _request_with_retry(
        "GET",
        f"{_base_url()}/v1/reference-data/locations",
        params={"subType": "CITY", "keyword": destination, "page[limit]": 1},
        headers=_auth_headers(),
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json().get("data", [])
    if not results:
        raise ValueError(f"Could not resolve '{destination}' to an airport/city code")
    return results[0]["iataCode"]


def _parse_duration(iso_duration: str) -> int:
    # e.g. "PT2H30M" -> 150 minutes
    hours = minutes = 0
    num = ""
    for ch in iso_duration.replace("PT", ""):
        if ch.isdigit():
            num += ch
        elif ch == "H":
            hours = int(num or 0)
            num = ""
        elif ch == "M":
            minutes = int(num or 0)
            num = ""
    return hours * 60 + minutes


def _enrich_cheapest_day(origin: str, destination: str, departure_date: str) -> dict:
    """One Flight Offers Search call, only for the cheapest day, for real
    airline/stops/duration to show in the UI."""
    resp = _request_with_retry(
        "GET",
        f"{_base_url()}/v2/shopping/flight-offers",
        params={
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": 1,
            "max": 1,
            "nonStop": "false",
        },
        headers=_auth_headers(),
        timeout=15,
    )
    resp.raise_for_status()
    body = resp.json()
    offers = body.get("data", [])
    if not offers:
        return {}

    offer = offers[0]
    itinerary = offer["itineraries"][0]
    segments = itinerary["segments"]
    carrier_code = segments[0]["carrierCode"]
    carriers = body.get("dictionaries", {}).get("carriers", {})
    return {
        "airline": carriers.get(carrier_code, carrier_code),
        "stops": len(segments) - 1,
        "duration_min": _parse_duration(itinerary["duration"]),
    }


def search_flights_real(destination: str, start_date: str, end_date: str, origin: str = "AMS") -> dict:
    origin_code = origin.upper()
    dest_code = resolve_iata(destination)

    resp = _request_with_retry(
        "GET",
        f"{_base_url()}/v1/shopping/flight-dates",
        params={
            "origin": origin_code,
            "destination": dest_code,
            "departureDate": f"{start_date},{end_date}",
            "oneWay": "true",
            "nonStop": "false",
        },
        headers=_auth_headers(),
        timeout=15,
    )
    resp.raise_for_status()
    entries = resp.json().get("data", [])
    if not entries:
        raise ValueError(f"Amadeus returned no fares for {origin_code}->{dest_code} in that window")

    days = [
        {
            "date": e["departureDate"],
            "price": float(e["price"]["total"]),
            "currency": "EUR",
        }
        for e in entries
    ]
    days.sort(key=lambda d: d["date"])

    cheapest = min(days, key=lambda d: d["price"])
    cheapest.update(_enrich_cheapest_day(origin_code, dest_code, cheapest["date"]))

    return {
        "origin": origin_code,
        "destination": destination,
        "destination_iata": dest_code,
        "days": days,
        "cheapest": cheapest,
        "source": f"Amadeus ({os.environ.get('AMADEUS_ENV', 'test')} environment)",
    }
