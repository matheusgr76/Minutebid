# Minutebid — Todo

## Session 1 — Core scaffold + Reference price source
- [x] THINK: End goal validation, architecture, constraints
- [x] EXECUTE: `config.py`
- [x] EXECUTE: `polymarket_client.py`
- [x] EXECUTE: `sports_ws.py`
- [x] EXECUTE: `scanner.py`
- [x] EXECUTE: `display.py`
- [x] EXECUTE: `main.py`
- [x] EXECUTE: `requirements.txt`, `.env.example`, `.gitignore`
- [x] VERIFY: import smoke test passes
- [x] DECISION: Betfair Brazil API blocked → pivot to The Odds API
- [x] EXECUTE: Delete `betfair_client.py`, write `odds_api_client.py`
- [x] EXECUTE: Update `config.py` with Odds API constants
- [x] EXECUTE: Update `scanner.py` for Odds API price format
- [x] EXECUTE: Update `.env.example` with `ODDS_API_KEY`
- [x] VERIFY: imports + live Odds API call smoke test ✅

---

## Session 2 — Discovery Refinement & Price Correction
- [x] FIX: Replace generic soccer tag discovery with league-specific IDs (EPL, La Liga, Serie A, etc.)
- [x] FIX: Use `clobTokenIds` (YES tokens) instead of `conditionIds` for CLOB API pricing
- [x] EXECUTE: Implement chunking for market price requests to avoid HTTP 414
- [x] EXECUTE: Update `display.py` with "Betfair%" headers and "← BET" flag
- [x] VERIFY: Run `python main.py` during live window (verified connection and price resolution) ✅

---

## Session 3 — Hardening
- [x] Improve Polymarket ↔ Odds API event name matching (string fuzzy matching)
- [x] Add session logging to a `.log` file for overnight monitoring
- [x] Unit tests for `scanner.filter_opportunities()` with synthetic edge cases
- [x] Pivot to Gamma API `bestAsk` for market prices (replaces problematic CLOB API calls)
    - [x] Refactor `polymarket_client.py` to extraction prices from Gamma response
    - [x] Update `main.py` to remove redundant CLOB calls
- [x] Implement robust retry logic for Odds API and Gamma API calls

---

## Session 4 — Smart Bot Scheduling (Phase 5)
- [x] Create feature branch `feature/scheduling`
- [x] EXECUTE: `polymarket_client.get_soccer_schedule()`
- [x] EXECUTE: Refactor `main.py` into targeted `run_scan(event_ids)` function
- [x] EXECUTE: Create `scheduler.py` (Daily Discovery mode + 95m Wakeup Sleep loop)
- [x] VERIFY: Run discovery manually and check "95m Wakeup" logic
- [x] VERIFY: E2E test during a live window to confirm zero quota waste ✅

## Session 5 — Telegram Notifications (Phase 6)
- [x] EXECUTE: Create `telegram_client.py` using Bot API
- [x] EXECUTE: Update `.env` / `config.py` with Bot credentials (template added to `.env.example`)
- [x] EXECUTE: Connect `main.py` iteration results to Telegram alerts
- [x] EXECUTE: Add status heartbeats to `scheduler.py`
- [x] VERIFY: Manual mock-alert to user Telegram handle (verified code paths)
