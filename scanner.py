# scanner.py — Pure filter logic. No I/O, no API calls.
# Takes raw data from all clients and returns actionable opportunities.

import logging
from rapidfuzz import fuzz
from config import MIN_MINUTE, MAX_MINUTE, WIN_PROB_THRESHOLD

logger = logging.getLogger(__name__)

SECOND_HALF_PERIODS = {"2h", "2nd", "second", "2nd half", "second half", "sh"}


def filter_opportunities(
    events: list[dict],
    prices: dict[str, float],
    game_states: dict[str, dict],
) -> list[dict]:
    """
    Return opportunities where Polymarket already implies >= WIN_PROB_THRESHOLD
    confidence for one outcome during the 75-90+ minute window.
    Signal: go to Polymarket and bet on the leading outcome.
    """
    opportunities = []

    for event in events:
        event_id = str(event.get("id", ""))
        game_state = game_states.get(event_id)

        if not game_state:
            continue

        if not _is_in_target_window(game_state):
            continue

        best = _best_outcome(event, prices)
        if not best:
            continue

        if best["probability"] >= WIN_PROB_THRESHOLD:
            opportunities.append({
                "match": event.get("title", ""),
                "minute": game_state["minute"],
                "score": f"{game_state['home_score']} - {game_state['away_score']}",
                "outcome": best["outcome"],
                "poly_prob": best["probability"],
                "market_url": f"https://polymarket.com/event/{event.get('slug', event_id)}",
            })

    logger.info("Found %d opportunities", len(opportunities))
    return opportunities


def _is_in_target_window(game_state: dict) -> bool:
    """Return True if game minute and period match the configured window."""
    minute = game_state.get("minute", 0)
    period = game_state.get("period", "").lower().strip()

    in_minute_range = MIN_MINUTE <= minute <= MAX_MINUTE
    in_second_half = any(kw in period for kw in SECOND_HALF_PERIODS) if period else True

    return in_minute_range and in_second_half


def _best_outcome(event: dict, prices: dict[str, float]) -> dict | None:
    """Find outcome with highest Polymarket implied probability."""
    best_prob = 0.0
    best_name = None

    for market in event.get("markets", []):
        condition_id = market.get("conditionId") or market.get("condition_id", "")
        price = prices.get(condition_id)
        if price is not None and price > best_prob:
            best_prob = price
            best_name = market.get("question") or condition_id

    if best_name is None:
        return None
    return {"outcome": str(best_name), "probability": best_prob}


def _normalize(text: str) -> str:
    """Lowers, strips, and removes common soccer fluff."""
    if not text:
        return ""
    text = text.lower()
    # Remove common suffixes/prefixes
    removals = ["fc", "cf", "sc", "united", "city", "real", "atletico", "saint", "st.", "st ", "vs", " v ", "."]
    for r in removals:
        text = text.replace(r, " ")
    
    return " ".join(text.split())
