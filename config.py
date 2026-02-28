# config.py — All configurable constants for the Minutebid scanner.
# No business logic here. Change thresholds without touching other files.

# ---------------------------------------------------------------------------
# Polymarket API endpoints (public, no auth required)
# ---------------------------------------------------------------------------
GAMMA_API_BASE = "https://gamma-api.polymarket.com"
CLOB_API_BASE = "https://clob.polymarket.com"
SPORTS_WS_URL = "wss://sports-api.polymarket.com/ws"

# ---------------------------------------------------------------------------
# Soccer Discovery (Specific Leagues)
# High-liquidity leagues with reliable Polymarket series IDs or tag slugs
# ---------------------------------------------------------------------------
LEAGUE_SERIES_IDS = {
    'premier_league': '10188',
    'la_liga': '10193',
    'serie_a': '10203',
}
LEAGUE_TAG_SLUGS = {
    'bundesliga': 'bundesliga',
    'champions_league': 'ucl',
    'europa_league': 'uel',
}

# ---------------------------------------------------------------------------
# Filter thresholds
# ---------------------------------------------------------------------------
MIN_MINUTE = 75        # Only consider matches at or after this minute
MAX_MINUTE = 120       # Covers 90 + extra time
WIN_PROB_THRESHOLD = 0.80  # Minimum Polymarket implied probability to surface a market
MAX_WIN_PROB_THRESHOLD = 0.97  # Exclude near-resolved markets (CLOB suspends trading above this)
MAX_SCHEDULE_HOURS = 48    # Only monitor matches starting within this window
SCAN_INTERVAL_SLOW = 120   # 2-minute "Slow Pulse" interval during active monitoring

# ---------------------------------------------------------------------------
# Betting configuration (Session 17 — Automatic Betting)
# ---------------------------------------------------------------------------
MAX_BET_BUDGET_USD = 5.0    # Maximum USDC to spend per game session (hard cap)
BET_STAKE_USD = 1.0         # Fixed stake per bet in USDC
CLOB_HOST = "https://clob.polymarket.com"
CLOB_CHAIN_ID = 137         # Polygon mainnet

# ---------------------------------------------------------------------------
# Network settings
# ---------------------------------------------------------------------------
REQUEST_TIMEOUT_SECONDS = 10   # HTTP request timeout
WS_READ_TIMEOUT_SECONDS = 8    # Max time to wait for WebSocket messages
WS_MAX_MESSAGES = 50           # Max messages to read in one WebSocket session

