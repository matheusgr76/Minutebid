# trader.py — Places CLOB market orders on Polymarket.
# Single Responsibility: authenticate and submit one FOK order per call.
# All credential reads from env vars; never hardcoded.

import logging
import os

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds, MarketOrderArgs, OrderType

_SIDE_BUY = 0  # py-clob-client side constant: BUY=0, SELL=1

from config import CLOB_HOST, CLOB_CHAIN_ID

logger = logging.getLogger(__name__)


def _build_client() -> ClobClient:
    """Build an authenticated CLOB client from environment credentials."""
    pk = os.getenv("CLOB_PK", "").strip()
    api_key = os.getenv("CLOB_API_KEY", "").strip()
    api_secret = os.getenv("CLOB_API_SECRET", "").strip()
    api_passphrase = os.getenv("CLOB_API_PASSPHRASE", "").strip()

    missing = [name for name, val in [
        ("CLOB_PK", pk),
        ("CLOB_API_KEY", api_key),
        ("CLOB_API_SECRET", api_secret),
        ("CLOB_API_PASSPHRASE", api_passphrase),
    ] if not val]

    if missing:
        raise EnvironmentError(f"Missing CLOB credentials: {', '.join(missing)}")

    return ClobClient(
        host=CLOB_HOST,
        chain_id=CLOB_CHAIN_ID,
        key=pk,
        creds=ApiCreds(
            api_key=api_key,
            api_secret=api_secret,
            api_passphrase=api_passphrase,
        ),
    )


def place_order(token_id: str, stake_usdc: float) -> dict:
    """
    Place a Fill-or-Kill market order on the Polymarket CLOB.

    Args:
        token_id:   CLOB token ID for the YES outcome (clobTokenIds[0]).
        stake_usdc: Amount in USDC to spend (e.g. 1.0 = $1.00).

    Returns:
        Order response dict from py-clob-client (contains 'orderID', 'status').

    Raises:
        EnvironmentError: if any CLOB credential is missing.
        Exception:        on network failure or order rejection.
    """
    client = _build_client()

    order = client.create_market_order(
        MarketOrderArgs(
            token_id=token_id,
            amount=stake_usdc,
            side=_SIDE_BUY,
        )
    )

    resp = client.post_order(order, OrderType.FOK)
    logger.info("Order placed — token_id=%s stake=$%.2f response=%s", token_id, stake_usdc, resp)
    return resp


def is_credentials_configured() -> bool:
    """
    Returns True if all four CLOB env vars are present.
    Used by main.py to decide whether to attempt betting.
    """
    return all(
        os.getenv(k, "").strip()
        for k in ("CLOB_PK", "CLOB_API_KEY", "CLOB_API_SECRET", "CLOB_API_PASSPHRASE")
    )
