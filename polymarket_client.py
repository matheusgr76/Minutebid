# polymarket_client.py — HTTP calls to Gamma API and CLOB API.
# Single responsibility: fetch raw market data. No filtering logic here.

import logging
import requests
import time
from config import (
    GAMMA_API_BASE,
    CLOB_API_BASE,
    REQUEST_TIMEOUT_SECONDS,
    LEAGUE_SERIES_IDS,
    LEAGUE_TAG_SLUGS
)

logger = logging.getLogger(__name__)


def _with_retry(func, *args, max_retries=3, initial_delay=1, **kwargs):
    """Execution wrapper with exponential backoff for HTTP requests."""
    retries = 0
    while retries < max_retries:
        try:
            return func(*args, **kwargs)
        except (requests.exceptions.RequestException, Exception) as e:
            retries += 1
            if retries == max_retries:
                logger.error("Max retries reached for request. Last error: %s", e)
                return None
            
            delay = initial_delay * (2 ** (retries - 1))
            logger.warning("Request failed (%s). Retrying in %ds... (Attempt %d/%d)", 
                           e, delay, retries, max_retries)
            time.sleep(delay)
    return None


def _get(url: str, params: dict = None) -> dict | list | None:
    """Shared GET helper with timeout, error handling, and exponential backoff retry."""
    def make_req():
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()

    return _with_retry(make_req)


def get_active_soccer_events() -> tuple[list[dict], dict[str, float]]:
    """
    Fetch all active soccer events from specific leagues defined in config.
    Returns (all_events, market_prices) where market_prices maps condition_id -> bestAsk.
    """
    all_events = []
    seen_ids = set()
    market_prices = {}

    def add_events(data):
        if not isinstance(data, list):
            return
        for event in data:
            event_id = str(event.get("id"))
            if event_id not in seen_ids:
                all_events.append(event)
                seen_ids.add(event_id)
                
                # Extract prices directly from market data in Gamma response
                for market in event.get("markets", []):
                    cond_id = market.get("conditionId") or market.get("condition_id")
                    best_ask = market.get("bestAsk")
                    if cond_id and best_ask is not None:
                        try:
                            # bestAsk in Gamma is already 0.0-1.0 float string or float
                            market_prices[str(cond_id)] = float(best_ask)
                        except (ValueError, TypeError):
                            continue

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

    logger.info("Found %d unique active soccer events. Resolved %d prices from Gamma.", 
                len(all_events), len(market_prices))
    return all_events, market_prices


def get_market_prices(condition_ids: list[str]) -> dict[str, float]:
    """
    [DEPRECATED] Fetch best-ask prices from CLOB.
    Now unnecessary as Gamma API provides these prices directly.
    """
    logger.warning("get_market_prices is deprecated. Use get_active_soccer_events return value.")
    return {}
