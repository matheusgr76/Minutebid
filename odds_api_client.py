# odds_api_client.py — Fetch live in-play soccer odds from The Odds API.
# Used as reference price to detect mispriced Polymarket markets.
# Credentials are loaded from environment variables.

import logging
import os
import requests
from config import (
    ODDS_API_BASE,
    ODDS_API_SPORT,
    ODDS_API_REGIONS,
    ODDS_API_MARKETS,
    ODDS_API_ODDS_FORMAT,
    REQUEST_TIMEOUT_SECONDS
)

logger = logging.getLogger(__name__)

def _get_api_key() -> str | None:
    """Read API key from environment."""
    key = os.environ.get("ODDS_API_KEY")
    if not key:
        logger.warning("ODDS_API_KEY not set. Add it to your .env file.")
    return key

def get_live_soccer_reference_prices() -> dict[str, dict]:
    """
    Fetch in-play H2H markets for soccer from The Odds API.
    Returns a dict keyed by normalized event name:
        {
            "home v away": {
                "home": 0.72,
                "draw": 0.18,
                "away": 0.10,
            }
        }
    """
    api_key = _get_api_key()
    if not api_key:
        return {}

    url = f"{ODDS_API_BASE}/sports/{ODDS_API_SPORT}/odds/"
    params = {
        "apiKey": api_key,
        "regions": ODDS_API_REGIONS,
        "markets": ODDS_API_MARKETS,
        "oddsFormat": ODDS_API_ODDS_FORMAT,
        "live": "true"
    }

    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        logger.error("The Odds API request failed: %s", exc)
        return {}

    return _process_odds_data(data)

def _process_odds_data(data: list) -> dict[str, dict]:
    """Process raw API response into normalized probability map."""
    price_map: dict[str, dict] = {}
    
    for event in data:
        home_team = event.get("home_team", "").lower()
        away_team = event.get("away_team", "").lower()
        event_name = f"{home_team} v {away_team}"
        
        bookmaker_probs = []
        
        for bookmaker in event.get("bookmakers", []):
            # Focus on h2h market
            for market in bookmaker.get("markets", []):
                if market.get("key") != "h2h":
                    continue
                
                outcomes = market.get("outcomes", [])
                # We need exactly 3 outcomes for soccer H2H (Home, Away, Draw)
                if len(outcomes) < 2:
                    continue
                
                implied_probs = {}
                for outcome in outcomes:
                    name = outcome.get("name", "").lower()
                    price = outcome.get("price")
                    if price and price > 0:
                        # Price is decimal odds
                        implied_probs[name] = 1.0 / price
                
                if implied_probs:
                    bookmaker_probs.append(implied_probs)
        
        if not bookmaker_probs:
            continue
            
        # Average across bookmakers
        avg_probs = {}
        # Get all outcome names present in any bookmaker
        all_outcomes = set().union(*[b.keys() for b in bookmaker_probs])
        
        for outcome in all_outcomes:
            vals = [b[outcome] for b in bookmaker_probs if outcome in b]
            avg_probs[outcome] = sum(vals) / len(vals)
            
        # Normalize
        total = sum(avg_probs.values())
        if total > 0:
            price_map[event_name] = {k: round(v / total, 4) for k, v in avg_probs.items()}
            logger.debug("Odds API: %s -> %s", event_name, price_map[event_name])

    logger.info("The Odds API: processed %d events", len(price_map))
    return price_map
