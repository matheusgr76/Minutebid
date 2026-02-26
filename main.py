# main.py — Entry point. Run manually: `python main.py`
# One scan per invocation. No daemon loop.

import logging
import sys
from dotenv import load_dotenv

import polymarket_client
import scanner
import display
import telegram_client

# ---------------------------------------------------------------------------
# Logging — console + persistent file for traceability
# ---------------------------------------------------------------------------
def setup_logging():
    """Unifies logging for console and file across all entry points."""
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%H:%M:%S"
    
    # Check if handlers are already configured to avoid duplicate setup
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            datefmt=date_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler("minutebid_scan.log", encoding="utf-8")
            ]
        )
    return logging.getLogger("main")

logger = setup_logging()


def run_single_scan() -> None:
    """Performs one full scan across all active soccer events."""
    logger.info("--- Starting single scan iteration ---")
    
    # 1. Fetch active soccer events and their market prices from Gamma
    events, prices = polymarket_client.get_active_soccer_events()
    if not events:
        logger.info("No active soccer events found on Polymarket right now.")
        return

    # 2. Filter: find outcomes >= 80% on Polymarket in the 75-90+ min window
    opportunities = scanner.filter_opportunities(events, prices)
    display.print_results(opportunities)
    
    # 7. Notify via Telegram
    for opp in opportunities:
        telegram_client.send_opportunity_alert(opp)


def run() -> None:
    load_dotenv()  # Load .env for Odds API credentials
    logger.info("=== Minutebid orchestrator started ===")
    run_single_scan()
    logger.info("=== Orchestrator complete ===")


if __name__ == "__main__":
    run()
