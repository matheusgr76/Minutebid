# scanner.py — Pure filter logic. No I/O, no API calls.
# Takes raw data from Gamma API and returns actionable opportunities.
# Game minute is estimated from event startTime (no WebSocket required).

import logging
from datetime import datetime, timezone
from config import MIN_MINUTE, MAX_MINUTE, WIN_PROB_THRESHOLD

logger = logging.getLogger(__name__)


def filter_opportunities(
    events: list[dict],
    prices: dict[str, float],
) -> list[dict]:
    """
    Return opportunities where Polymarket already implies >= WIN_PROB_THRESHOLD
    confidence for one outcome during the 75-90+ minute window.
    Game minute is estimated from event startTime + elapsed real time.
    Signal: go to Polymarket and bet on the leading outcome.
    """
    opportunities = []
    now = datetime.now(timezone.utc)

    for event in events:
        event_id = str(event.get("id", ""))

        minute = _estimate_minute(event, now)
        if minute is None:
            continue

        if not (MIN_MINUTE <= minute <= MAX_MINUTE):
            continue

        best = _best_outcome(event, prices)
        if not best:
            continue

        if best["probability"] >= WIN_PROB_THRESHOLD:
            opportunities.append({
                "match": event.get("title", ""),
                "minute": minute,
                "outcome": best["outcome"],
                "poly_prob": best["probability"],
                "market_url": f"https://polymarket.com/event/{event.get('slug', event_id)}",
            })

    logger.info("Found %d opportunities", len(opportunities))
    return opportunities


def _estimate_minute(event: dict, now: datetime) -> int | None:
    """Estimate game minute from event startTime and current UTC time."""
    start_str = event.get("startTime")
    if not start_str:
        return None
    try:
        kickoff = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        elapsed_minutes = int((now - kickoff).total_seconds() / 60)
        return elapsed_minutes
    except (ValueError, TypeError):
        return None


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
