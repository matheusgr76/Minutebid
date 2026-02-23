# polymarket_client.py — HTTP calls to Gamma API and CLOB API.
# Single responsibility: fetch raw market data. No filtering logic here.

import logging
import requests
from config import (
    GAMMA_API_BASE,
    CLOB_API_BASE,
    REQUEST_TIMEOUT_SECONDS,
    LEAGUE_SERIES_IDS,
    LEAGUE_TAG_SLUGS
)

logger = logging.getLogger(__name__)


def _get(url: str, params: dict = None) -> dict | list | None:
    """Shared GET helper with timeout and error handling."""
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.error("Request timed out: %s", url)
    except requests.exceptions.HTTPError as exc:
        logger.error("HTTP error %s for %s", exc.response.status_code, url)
    except requests.exceptions.RequestException as exc:
        logger.error("Request failed for %s: %s", url, exc)
    return None


def get_active_soccer_events() -> list[dict]:
    """Fetch all active soccer events from specific leagues defined in config."""
    all_events = []
    seen_ids = set()

    def add_events(data):
        if not isinstance(data, list):
            return
        for event in data:
            event_id = str(event.get("id"))
            if event_id not in seen_ids:
                all_events.append(event)
                seen_ids.add(event_id)

    # 1. Fetch by Series IDs (Premier League, La Liga, Serie A)
    for league, series_id in LEAGUE_SERIES_IDS.items():
        logger.debug("Fetching %s events (series %s)", league, series_id)
        params = {"series_id": series_id, "active": "true", "closed": "false"}
        data = _get(f"{GAMMA_API_BASE}/events", params=params)
        add_events(data)

    # 2. Fetch by Tag Slugs (Bundesliga, Champions League)
    for league, tag_slug in LEAGUE_TAG_SLUGS.items():
        logger.debug("Fetching %s events (tag %s)", league, tag_slug)
        params = {"tag_slug": tag_slug, "active": "true", "closed": "false"}
        data = _get(f"{GAMMA_API_BASE}/events", params=params)
        add_events(data)

    logger.info("Found %d unique active soccer events across targeted leagues", len(all_events))
    return all_events


def get_market_prices(condition_ids: list[str]) -> dict[str, float]:
    """
    Fetch best-ask prices for YES tokens on the CLOB API.
    Returns {condition_id: implied_probability} where 0.85 means 85%.
    """
    if not condition_ids:
        return {}

    prices = {}
    # Chunk IDs to avoid HTTP 414 (URI Too Long)
    # 20 IDs per request is safe for most browsers/servers
    chunk_size = 20
    for i in range(0, len(condition_ids), chunk_size):
        chunk = condition_ids[i : i + chunk_size]
        params = {"token_ids": ",".join(chunk)}
        data = _get(f"{CLOB_API_BASE}/midpoints", params=params)

        if not isinstance(data, dict):
            continue

        for condition_id, price_str in data.items():
            try:
                prices[condition_id] = float(price_str)
            except (ValueError, TypeError):
                logger.debug("Unparseable price for %s: %s", condition_id, price_str)

    logger.info("Resolved prices for %d markets", len(prices))
    return prices
