# scanner.py — Pure filter logic. No I/O, no API calls.
# Takes raw data from all clients and returns actionable opportunities.

import logging
from rapidfuzz import fuzz
from config import MIN_MINUTE, MAX_MINUTE, WIN_PROB_THRESHOLD, MIN_EDGE_THRESHOLD, RESOLVED_ODDS_THRESHOLD

logger = logging.getLogger(__name__)

SECOND_HALF_PERIODS = {"2h", "2nd", "second", "2nd half", "second half", "sh"}


def filter_opportunities(
    events: list[dict],
    prices: dict[str, float],
    game_states: dict[str, dict],
    reference_prices: dict[str, dict],
) -> list[dict]:
    """
    Return opportunities where the match is statistically resolved by bookmakers.
    Threshold: odds < 1.05 (implied prob > 95.2%).
    """
    opportunities = []

    # Calculate probability threshold from odds (e.g., 1/1.05 = 0.952)
    PROB_THRESHOLD = round(1.0 / RESOLVED_ODDS_THRESHOLD, 4)

    for event in events:
        event_id = str(event.get("id", ""))
        game_state = game_states.get(event_id)

        if not game_state:
            continue

        if not _is_in_target_window(game_state):
            continue

        # Find the favorite based on bookmaker prices, not Polymarket
        # We look for ANY outcome resolved by bookies
        event_title = event.get("title", "")
        ref_match = _lookup_reference_event(event, reference_prices)
        
        if not ref_match:
            continue

        ref_outcomes = reference_prices[ref_match]
        for outcome_name, ref_prob in ref_outcomes.items():
            if ref_prob >= PROB_THRESHOLD:
                # Found a statistically resolved outcome
                # Now quickly check Polymarket price for this specific outcome
                poly_prob = _lookup_poly_prob(event, outcome_name, prices)
                
                opportunities.append({
                    "match": event_title,
                    "minute": game_state["minute"],
                    "score": f"{game_state['home_score']} - {game_state['away_score']}",
                    "resolved_outcome": outcome_name,
                    "reference_prob": ref_prob,
                    "poly_prob": poly_prob,
                    "market_url": f"https://polymarket.com/event/{event.get('slug', event_id)}",
                })
                # Only one resolved outcome per match is likely
                break

    logger.info("Found %d resolved opportunities", len(opportunities))
    return opportunities


def _lookup_reference_event(
    event: dict,
    reference_prices: dict[str, dict],
) -> str | None:
    """
    Try to match this event to a Reference market using fuzzy matching.
    Returns the name of the best matching reference event, or None.
    """
    event_title = _normalize(event.get("title", ""))
    
    best_event_match = None
    best_event_score = 0.0
    
    for ref_event_name in reference_prices.keys():
        score = fuzz.token_set_ratio(event_title, _normalize(ref_event_name))
        if score > best_event_score:
            best_event_score = score
            best_event_match = ref_event_name

    # Threshold for event matching: 80% with token_set_ratio is very safe
    if not best_event_match or best_event_score < 80:
        logger.debug("No reference event match for '%s' (Best score: %s)", event_title, best_event_score)
        return None
    
    return best_event_match


def _lookup_poly_prob(
    event: dict,
    outcome_name: str,
    prices: dict[str, float],
) -> float | None:
    """
    Find the Polymarket implied probability for a specific outcome within an event.
    """
    norm_outcome = _normalize(outcome_name)
    
    best_poly_prob = None
    best_outcome_score = 0.0

    for market in event.get("markets", []):
        market_question = _normalize(market.get("question", ""))
        score = fuzz.token_set_ratio(norm_outcome, market_question)
        
        if score > best_outcome_score:
            condition_id = market.get("conditionId") or market.get("condition_id", "")
            price = prices.get(condition_id)
            if price is not None:
                best_outcome_score = score
                best_poly_prob = price
    
    # A reasonable threshold for matching the outcome name
    if best_outcome_score > 70:
        return best_poly_prob
    
    return None


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
    Try to match this event to a Reference market using fuzzy matching.
    """
    event_title = _normalize(event.get("title", ""))
    
    # 1. Find the best matching event in Reference Prices
    best_event_match = None
    best_event_score = 0.0
    
    for ref_event_name in reference_prices.keys():
        score = fuzz.token_set_ratio(event_title, _normalize(ref_event_name))
        if score > best_event_score:
            best_event_score = score
            best_event_match = ref_event_name

    # Threshold for event matching: 80% with token_set_ratio is very safe
    if not best_event_match or best_event_score < 80:
        logger.debug("No reference event match for '%s' (Best score: %s)", event_title, best_event_score)
        return None

    # 2. Find the best matching outcome within that event
    outcomes = reference_prices[best_event_match]
    
    # Special Handling for Draws
    if "draw" in outcome_name.lower():
        return outcomes.get("Draw") or outcomes.get("draw")

    # Fuzzy match for team names in the question
    # e.g. "Will Liverpool win?" matched against Reference "Liverpool"
    best_outcome_match = None
    best_outcome_score = 0.0
    
    norm_outcome = _normalize(outcome_name)

    for ref_outcome_name, prob in outcomes.items():
        score = fuzz.token_set_ratio(norm_outcome, _normalize(ref_outcome_name))
        if score > best_outcome_score:
            best_outcome_score = score
            best_outcome_match = prob
            
    if best_outcome_score > 70:
        return best_outcome_match

    return None


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
