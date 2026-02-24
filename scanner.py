# scanner.py — Pure filter logic. No I/O, no API calls.
# Takes raw data from all clients and returns actionable opportunities.

import logging
import difflib
from config import MIN_MINUTE, MAX_MINUTE, WIN_PROB_THRESHOLD, MIN_EDGE_THRESHOLD

logger = logging.getLogger(__name__)

SECOND_HALF_PERIODS = {"2h", "2nd", "second", "2nd half", "second half", "sh"}


def filter_opportunities(
    events: list[dict],
    prices: dict[str, float],
    game_states: dict[str, dict],
    reference_prices: dict[str, dict],
) -> list[dict]:
    """
    Return opportunities matching all conditions:
      1. Match is in minute range [MIN_MINUTE, MAX_MINUTE]
      2. Match is in second half
      3. At least one outcome has Polymarket implied prob > WIN_PROB_THRESHOLD

    Edge (Reference prob - Polymarket prob) is computed when Reference data is available.
    Opportunities with positive edge are flagged; all qualifying matches are shown.
    """
    opportunities = []

    for event in events:
        event_id = str(event.get("id", ""))
        game_state = game_states.get(event_id)

        if not game_state:
            logger.debug("No game state for event %s — skipping", event_id)
            continue

        if not _is_in_target_window(game_state):
            continue

        best = _best_outcome(event, prices)
        if best is None or best["probability"] <= WIN_PROB_THRESHOLD:
            continue

        ref_prob = _lookup_reference_prob(event, best["outcome"], reference_prices)
        edge = round(ref_prob - best["probability"], 4) if ref_prob is not None else None

        opportunities.append({
            "match": event.get("title", "Unknown Match"),
            "minute": game_state["minute"],
            "score": f"{game_state['home_score']} - {game_state['away_score']}",
            "leader": best["outcome"],
            "poly_prob": best["probability"],
            "reference_prob": ref_prob,
            "edge": edge,
            "market_url": f"https://polymarket.com/event/{event.get('slug', event_id)}",
        })

    logger.info("Found %d qualifying opportunities", len(opportunities))
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


def _lookup_reference_prob(
    event: dict,
    outcome_name: str,
    reference_prices: dict[str, dict],
) -> float | None:
    """
    Try to match this event to a Reference market using fuzzy matching,
    then return the probability for the matching outcome.
    """
    event_title = event.get("title", "").lower()
    
    # 1. Find the best matching event
    best_event_match = None
    best_event_score = 0.0
    
    for ref_event_name in reference_prices.keys():
        score = _calculate_similarity(event_title, ref_event_name.lower())
        if score > best_event_score:
            best_event_score = score
            best_event_match = ref_event_name

    # Threshold for event matching: 0.6 is usually safe for team names
    if not best_event_match or best_event_score < 0.6:
        return None

    # 2. Find the best matching outcome within that event
    outcomes = reference_prices[best_event_match]
    outcome_lower = outcome_name.lower()
    
    # Simple check first: Does the team name appear in the question?
    # e.g. "Will Liverpool win?" matches "Liverpool"
    best_outcome_match = None
    best_outcome_score = 0.0

    for ref_outcome_name, prob in outcomes.items():
        ref_lower = ref_outcome_name.lower()
        # Direct containment is common
        if ref_lower in outcome_lower or outcome_lower in ref_lower:
            return prob
            
        # Fuzzy fallback for outcomes
        score = _calculate_similarity(outcome_lower, ref_lower)
        if score > best_outcome_score:
            best_outcome_score = score
            best_outcome_match = prob
            
    if best_outcome_score > 0.5:
        return best_outcome_match

    return None


def _calculate_similarity(a: str, b: str) -> float:
    """Return a similarity score between 0.0 and 1.0."""
    # Remove common junk words
    stop_words = {"vs", "v", "fc", "the", "a", "an", "and", "&"}
    a_clean = " ".join([w for w in a.split() if w not in stop_words])
    b_clean = " ".join([w for w in b.split() if w not in stop_words])
    
    return difflib.SequenceMatcher(None, a_clean, b_clean).ratio()
