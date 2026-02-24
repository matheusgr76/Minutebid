# Minutebid — Final Project Handoff

## Overview
Minutebid is a live soccer probability scanner that identifies mispriced winner markets on Polymarket. It targets the 75-90 minute window of matches when win probabilities (implied by prices) should be high for the leader.

---

## Current System Architecture

### 1. Data Sources
- **Polymarket Gamma API**: Primary source for market discovery and **real-time prices** (`bestAsk`).
- **Polymarket Sports WebSocket**: Source for live match state (minute, score).
- **The Odds API**: Reference source for "sharp" market probabilities from external bookmakers.

### 2. Core Components
- `polymarket_client.py`: Handles discovery of soccer events and extraction of "Yes" token prices.
- `sports_ws.py`: Maintains a real-time map of live soccer game states.
- `odds_api_client.py`: Fetches and averages probabilities from multiple external bookmakers.
- `scanner.py`: The "brain" — correlations events, applies fuzzy matching for team names, and calculates "Edge".
- `display.py`: Renders the results in a clean CLA table.
- `main.py`: Orchestrates the scan.

---

## Key Features (Session 3 Hardening)

- **Gamma API Pivot**: Removed dependencies on the unstable CLOB API. Prices are now fetched directly from Gamma, resolving persistent "Bad Request" errors.
- **Fuzzy Matching**: Uses `difflib` to match "Everton" (Polymarket) with "Everton FC" (Odds API) automatically.
- **Robustness**: All API calls include exponential backoff retry logic.
- **Logging**: All activity is logged to `minutebid_scan.log` for traceability.
- **Testing**: Unit tests in `tests/test_scanner.py` verify filtering logic.

---

## Upcoming: Phase 5 - Smart Daily Scheduler (Quota Aware)
To protect the Odds API quota, the bot is moving to a "Smart Discovery" model:
1. **Manual Discovery**: User runs the bot once a day.
2. **Schedule Mapping**: Bot identifies soccer matches starting in the next 24h.
3. **Smart Sleep**: Bot sleeps until the **"95-minute anchor"** (StartTime + 95m), which targets the Minute 75-90+ window after accounting for half-time and stoppage.
4. **Active Scanning**: WebSocket is used to track the *actual* game clock; Odds API is ONLY called during the target window.

---

## How to Run

1. **Environment**: Ensure `.env` contains:
   ```text
   ODDS_API_KEY=your_key_here
   ```
2. **Execution**:
   ```bash
   python main.py
   ```
3. **Output**:
   The scanner prints a table of opportunities where:
   - `Lead` matches the winner token.
   - `Poly%` < `Ref%` (positive edge).
   - Time is between 75' and 90'.

---

## Next Steps / Future Work
- **Automated Betting**: Integrate Polymarket CLOB order placement (API key and wallet required).
- **Telegram/Discord Notifications**: Push opportunities to a channel instead of just printing to console.
- **Broader Market Support**: Extend to other sports or categories using similar logic.

---

## Maintenance
- **Logs**: Rotate `minutebid_scan.log` if it grows too large.
- **Fuzzy Thresholds**: Adjust similarity thresholds in `scanner.py` (`_lookup_reference_prob`) if too many false positives/negatives occur.
