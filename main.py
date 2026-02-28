# main.py — Entry point. Run manually: `python main.py`
# One scan per invocation. No daemon loop.

import logging
import sys
from dotenv import load_dotenv

import polymarket_client
import scanner
import display
import telegram_client
import trader
from config import BET_STAKE_USD
from risk_manager import RiskManager

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


def run_single_scan(risk_manager: RiskManager = None) -> None:
    """
    Performs one full scan across all active soccer events.

    Args:
        risk_manager: Optional session-scoped RiskManager. If provided, bet
                      placement is attempted after each Telegram alert.
                      If None, the scan runs in alert-only mode (no orders placed).
    """
    logger.info("--- Starting single scan iteration ---")

    # 1. Fetch active soccer events and their market prices from Gamma
    events, prices = polymarket_client.get_active_soccer_events()
    if not events:
        logger.info("No active soccer events found on Polymarket right now.")
        return

    # 2. Filter: find outcomes >= 80% on Polymarket in the 75-90+ min window
    opportunities = scanner.filter_opportunities(events, prices)
    display.print_results(opportunities)

    betting_active = risk_manager is not None and trader.is_credentials_configured()
    if risk_manager is not None and not betting_active:
        logger.warning("RiskManager provided but CLOB credentials missing — running alert-only.")

    for opp in opportunities:
        # Always send Telegram alert regardless of betting mode
        telegram_client.send_opportunity_alert(opp)

        if not betting_active:
            continue

        token_id = opp.get("token_id")
        if not token_id:
            logger.warning("No token_id for '%s' — skipping bet.", opp["match"])
            continue

        approved, reason = risk_manager.approve(token_id)
        if not approved:
            logger.info("Bet skipped for '%s': %s", opp["match"], reason)
            continue

        try:
            result = trader.place_order(token_id, BET_STAKE_USD)
            risk_manager.record_bet(token_id)
            telegram_client.send_order_confirmation(opp, result, BET_STAKE_USD)
        except Exception as e:
            logger.error("Order failed for '%s': %s", opp["match"], e)
            telegram_client.send_order_failure(opp, str(e))


def run() -> None:
    load_dotenv()
    logger.info("=== Minutebid orchestrator started ===")
    run_single_scan()  # alert-only when invoked standalone
    logger.info("=== Orchestrator complete ===")


if __name__ == "__main__":
    run()
