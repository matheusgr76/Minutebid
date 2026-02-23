# sports_ws.py — Read live game state from Polymarket's Sports WebSocket.
# Single responsibility: connect, read one batch of messages, return game states.

import json
import logging
import websocket
from config import SPORTS_WS_URL, WS_READ_TIMEOUT_SECONDS, WS_MAX_MESSAGES

logger = logging.getLogger(__name__)


def get_live_game_states() -> dict[str, dict]:
    """
    Connect to the Sports WebSocket, read up to WS_MAX_MESSAGES messages,
    and return a dict of live game states keyed by event_id.

    Returned structure per event:
        {
            "minute": int,
            "period": str,        # e.g. "2H", "HT", "FT"
            "home_score": int,
            "away_score": int,
        }

    Returns an empty dict if connection fails or no data is received.
    """
    game_states: dict[str, dict] = {}

    try:
        ws = websocket.create_connection(
            SPORTS_WS_URL,
            timeout=WS_READ_TIMEOUT_SECONDS,
        )
        logger.info("Sports WebSocket connected")
    except Exception as exc:
        logger.error("Failed to connect to Sports WebSocket: %s", exc)
        return game_states

    try:
        for _ in range(WS_MAX_MESSAGES):
            try:
                raw = ws.recv()
            except websocket.WebSocketTimeoutException:
                logger.info("WebSocket read timeout — stopping message collection")
                break

            _parse_and_store(raw, game_states)
    finally:
        ws.close()

    logger.info("Collected game states for %d events", len(game_states))
    return game_states


def _parse_and_store(raw: str, game_states: dict) -> None:
    """Parse one WebSocket message and upsert into game_states."""
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError:
        logger.debug("Skipping non-JSON WebSocket message")
        return

    event_id = msg.get("event_id") or msg.get("eventId")
    if not event_id:
        return

    minute = _extract_minute(msg)
    if minute is None:
        return

    game_states[str(event_id)] = {
        "minute": minute,
        "period": msg.get("period") or msg.get("half") or "",
        "home_score": int(msg.get("home_score", 0) or msg.get("homeScore", 0)),
        "away_score": int(msg.get("away_score", 0) or msg.get("awayScore", 0)),
    }


def _extract_minute(msg: dict) -> int | None:
    """Extract game minute from a WebSocket message, trying known field names."""
    for key in ("minute", "game_minute", "time", "clock"):
        val = msg.get(key)
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                continue
    return None
