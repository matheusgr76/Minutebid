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

---

## Session 6 — Scanner Hardening (Phase 7)
- [x] EXECUTE: Install `rapidfuzz` for string metric matching
- [x] EXECUTE: Implement name normalization (lowercase, trim suffixes like "FC" or "United")
- [x] EXECUTE: Update `scanner.py` to use fuzzy thresholds (Token Set Ratio) when exact match fails
- [x] VERIFY: Run tests with a list of known variations (e.g., "Arsenal FC" vs "Arsenal") ✅
## Session 7 — Scheduler UI (Telegram Monitoring)
- [x] THINK: Design Telegram summary format with countdowns
- [x] EXECUTE: Update `telegram_client.py` with `update_scheduler_dashboard` (send/edit live dashboard with T-minus countdowns, 15-game cap)
- [x] EXECUTE: Update `scheduler.py` to call dashboard after discovery
- [x] FIX: Throttle `update_scheduler_dashboard` to 300s interval — dashboard is monitoring-only; alerts handle real-time opportunity delivery
- [x] VERIFY: Run scheduler and verify Telegram dashboard output and update cadence ✅
- [x] FIX: Deduplicate schedule entries by normalized title — Polymarket emits "Match X" and "Match X - More Markets" as separate events; strip known suffixes and check `seen_titles` to keep only the canonical entry

---

## Session 8 — Hotfix: Wakeup Delay & Stability
- [x] Create hotfix branch `hotfix/wakeup-and-stability` off `main`
- [x] EXECUTE: Reduce `WAKEUP_DELAY_MINUTES` to 80 in `scheduler.py`
- [x] EXECUTE: Add try/except to `update_scheduler_dashboard` in `scheduler.py`
- [x] EXECUTE: Enhance error handling in `telegram_client.py`
- [x] EXECUTE: Convert all displays (Dashboard, Logs) to UTC-3 (Brasilia Time)
- [x] VERIFY: Restart scheduler and confirm dashboard updates in UTC-3
- [x] Merge `hotfix/wakeup-and-stability` into `main` ✅

---

## Session 9 — Slow Pulse Monitoring (Phase 9)
- [x] Create feature branch `feature/slow-pulse-monitoring` ✅
- [x] EXECUTE: Add constants to `config.py` (`SCAN_INTERVAL_SLOW`, `RESOLVED_ODDS_THRESHOLD`) ✅
- [x] EXECUTE: Modify `scheduler.py` to use `SCAN_INTERVAL_SLOW` (120s) during active sessions ✅
- [x] EXECUTE: Simplify `scanner.py` to focus on bookmaker odds threshold instead of edge/prob ✅
- [x] EXECUTE: Update `main.py` to reflect the simplified scanning flow ✅
- [x] VERIFY: Run bot and verify 2-minute cadence and threshold detection ✅

---

## Session 10 — Dashboard Reliability (Phase 10)
- [x] Refactor `scheduler.py` to move dashboard update logic into a helper function. ✅
- [x] Inject the helper function into the active monitoring loop. ✅
- [x] Reduce `dashboard_interval` to 120s for better responsiveness. ✅
- [x] Verify that the dashboard updates while a match is "ACTIVE". ✅

---

## Session 11 — Always On (Local Windows Persistence)
- [x] THINK: Research options and billing risks ✅
- [x] EXECUTE: Implement Windows sleep prevention ✅
- [x] VERIFY: Confirm 24/7 persistence via Telegram ✅
- [x] CLEANUP: Remove unused cloud config files (Dockerfile, scripts) ✅

---

## Session 13 — Telegram Dashboard Refactor (Hotfix)
- [x] THINK: Plan re-post logic and 10min frequency ✅
- [x] EXECUTE: Modify `scheduler.py` intervals and re-post trigger ✅
- [x] EXECUTE: Update `telegram_client.py` message handling ✅
- [ ] VERIFY: Monitor dashboard creation and edit cycle

---

## Session 14 — Cloud Deployment (Phase 14)
- [ ] THINK: Select cloud provider (GCP/AWS/Azure) vs Dedicated VPS
- [ ] THINK: Plan environment migration (Secrets, UTC-3 sync, inhibition)
- [ ] EXECUTE: Setup cloud instance and deploy code

---

## Session 15 — Automatic Betting System (Phase 15)
- [ ] THINK: Define risk management and staking logic
- [ ] THINK: Evaluate Polymarket CLOB API vs Proxy for automated execution
- [ ] EXECUTE: Implement order placement logic (Smart Betting)
