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
- [ ] Improve Polymarket ↔ Odds API event name matching (string fuzzy matching)
- [ ] Implement robust retry logic for CLOB API temporary bottlenecks
- [ ] Unit tests for `scanner.filter_opportunities()` with synthetic edge cases
- [ ] Add session logging to a `.log` file for overnight monitoring
