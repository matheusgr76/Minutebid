# main.py — Entry point. Run manually: `python main.py`
# One scan per invocation. No daemon loop.

import logging
import sys
from dotenv import load_dotenv

import polymarket_client
import sports_ws
import odds_api_client
import scanner
import display

# ---------------------------------------------------------------------------
# Logging — timestamps + module names for traceability
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("main")


def run() -> None:
    load_dotenv()  # Load .env for Odds API credentials
    logger.info("=== Minutebid scan started ===")

    # 1. Fetch active soccer events from targeted leagues
    events = polymarket_client.get_active_soccer_events()
    if not events:
        print("\n  No active soccer events found on Polymarket right now.\n")
        return

    # 3. Gather all YES token IDs and map them to condition IDs
    import json
    token_to_condition = {}
    for event in events:
        for market in event.get("markets", []):
            cond_id = market.get("conditionId") or market.get("condition_id")
            token_ids_str = market.get("clobTokenIds")
            if cond_id and token_ids_str:
                try:
                    token_ids = json.loads(token_ids_str)
                    if token_ids and len(token_ids) > 0:
                        yes_token_id = str(token_ids[0])
                        token_to_condition[yes_token_id] = str(cond_id)
                except (json.JSONDecodeError, TypeError):
                    continue

    token_ids = list(token_to_condition.keys())
    raw_prices = polymarket_client.get_market_prices(token_ids)
    
    # Map raw token prices back to condition IDs for the scanner
    prices = {token_to_condition[tid]: price for tid, price in raw_prices.items()}

    # 4. Fetch live game states via Sports WebSocket
    game_states = sports_ws.get_live_game_states()

    # 5. Fetch Odds API reference prices (graceful if credentials missing)
    reference_prices = odds_api_client.get_live_soccer_reference_prices()

    # 6. Filter and display
    opportunities = scanner.filter_opportunities(events, prices, game_states, reference_prices)
    display.print_results(opportunities)

    logger.info("=== Scan complete ===")


if __name__ == "__main__":
    run()
