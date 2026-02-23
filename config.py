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
}

# ---------------------------------------------------------------------------
# Filter thresholds
# ---------------------------------------------------------------------------
MIN_MINUTE = 75        # Only consider matches at or after this minute
MAX_MINUTE = 120       # Covers 90 + extra time
WIN_PROB_THRESHOLD = 0.80  # Minimum implied probability to surface a market

# ---------------------------------------------------------------------------
# Network settings
# ---------------------------------------------------------------------------
REQUEST_TIMEOUT_SECONDS = 10   # HTTP request timeout
WS_READ_TIMEOUT_SECONDS = 8    # Max time to wait for WebSocket messages
WS_MAX_MESSAGES = 50           # Max messages to read in one WebSocket session

# ---------------------------------------------------------------------------
# The Odds API (reference price / edge detection)
# Credentials loaded from .env — never hardcoded here
# ---------------------------------------------------------------------------
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
ODDS_API_SPORT = "soccer"          # The Odds API sport key for all soccer
ODDS_API_REGIONS = "eu"
ODDS_API_MARKETS = "h2h"
ODDS_API_ODDS_FORMAT = "decimal"

# Minimum edge (Reference prob - Polymarket prob) to flag as mispriced
# e.g. 0.05 means Reference must price at least 5pp higher than Polymarket
MIN_EDGE_THRESHOLD = 0.05
