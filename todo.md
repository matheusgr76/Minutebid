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
- [x] VERIFY: Monitor dashboard creation and edit cycle ✅

---

## Session 14 — Cloud Deployment (Koyeb)
- [x] THINK: Select cloud provider → Koyeb free tier (Worker service, always-on, 1 container) ✅
- [x] THINK: Plan environment migration (secrets via Koyeb UI, Linux compat, ephemeral state) ✅
- [x] EXECUTE: Add `import platform` guard to `scheduler.py` (Linux-safe sleep inhibition) ✅
- [x] EXECUTE: Create `Dockerfile` (python:3.12-slim, PYTHONUNBUFFERED=1) ✅
- [x] EXECUTE: Create `.dockerignore` ✅
- [x] EXECUTE: Update `todo.md` and `implementation_plan.md` ✅
- [x] EXECUTE: Merge `hotfix/telegram-dashboard-refactor` → `main` and push to GitHub ✅
- [x] VERIFY: Create Koyeb Worker service, set env vars, deploy, confirm "Smart Scheduler Started 🚀" via Telegram ✅

---

## Session 15 — Scanner Pivot: Polymarket-Only (Hotfix)
- [x] THINK: Root cause — `ODDS_API_SPORT = "soccer"` is invalid key + free tier has no live odds → scanner never fired ✅
- [x] THINK: Decision — drop Odds API entirely, alert on Polymarket price >= 80% during 75-90+ min ✅
- [x] EXECUTE: Simplify `scanner.py` to Polymarket-only (remove `reference_prices` param) ✅
- [x] EXECUTE: Remove Odds API call from `main.py` ✅
- [x] EXECUTE: Update `telegram_client.py` alert format ✅
- [x] EXECUTE: Remove dead constants from `config.py` ✅
- [x] EXECUTE: Delete `odds_api_client.py` ✅
- [x] VERIFY: Confirm bet signal fires correctly during next live match ✅

---

## Session 15b — Add UEL (UEFA Europa League)
- [x] EXECUTE: Add `'europa_league': 'uel'` to `LEAGUE_TAG_SLUGS` in `config.py` ✅
- [x] VERIFY: Confirmed UEL matches appear in daily discovery dashboard ✅

---

## Session 16 — Fix: Drop Broken WebSocket, Use Time-Based Minute
- [x] THINK: Root cause — Sports WebSocket returns 0 events every scan; missing subscription message ✅
- [x] THINK: Decision — drop WebSocket, estimate minute from Gamma API `startTime` + elapsed time ✅
- [x] EXECUTE: Rewrite `scanner.py` — `_estimate_minute()` replaces `game_states` lookup ✅
- [x] EXECUTE: Remove `sports_ws` import/call from `main.py` ✅
- [x] EXECUTE: Remove score line from `telegram_client.py` alert, add `~` prefix to minute ✅
- [x] EXECUTE: Delete `sports_ws.py` ✅
- [x] VERIFY: Bet signal confirmed firing during live games ✅

---

## Session 16b — Fix: display.py Silent Crash on Bet Signal
- [x] THINK: Root cause — `display.print_results()` referenced stale fields (`reference_prob`, `resolved_outcome`, `score`) from pre-pivot era; crashed with `KeyError` on every real opportunity, killing Telegram alert before it sent ✅
- [x] EXECUTE: Update `display.py` print loop to use current fields (`outcome`, `poly_prob`) ✅
- [x] VERIFY: Telegram alerts confirmed firing end-to-end ✅

---

## Session 17 — Automatic Betting (Phase 17) ✅ LIVE
Branch `feature/automatic-betting` merged to `main` and deployed to Koyeb.

### Prerequisites
- [x] Signal quality validated — multiple live signals confirmed correct, manual execution too slow ✅
- [x] Polymarket account ready ✅
- [x] $14 USDC already on Polymarket (CLOB draws from proxy wallet — no transfer needed) ✅
- [x] CLOB API key + secret + passphrase generated in Polymarket UI ✅
- [x] Wallet private key exported from Crypto.com DeFi wallet ✅
- [x] All four CLOB credentials added to Koyeb env vars as Secrets ✅

### Architecture Design
- [x] THINK: Flat stake ($1/bet) chosen over Kelly — simpler, safer for initial trials ✅
- [x] THINK: RiskManager design — $5 budget cap/session, duplicate token guard ✅
- [x] THINK: FOK market orders chosen — immediate fill or cancel, no stale orders post-whistle ✅
- [x] THINK: Failure modes documented — token_id None, FOK no-fill, auth error, duplicate signal ✅

### Implementation
- [x] EXECUTE: `risk_manager.py` — session-scoped RiskManager, approve/record_bet ✅
- [x] EXECUTE: `trader.py` — `place_order(token_id, stake_usdc)` + `is_credentials_configured()` ✅
- [x] EXECUTE: `scanner.py` — added `token_id` (clobTokenIds[0]) to opportunity dict ✅
- [x] EXECUTE: `config.py` — `MAX_BET_BUDGET_USD=5.0`, `BET_STAKE_USD=1.0`, `CLOB_HOST`, `CLOB_CHAIN_ID` ✅
- [x] EXECUTE: `main.py` — `run_single_scan(risk_manager=None)`; alert-only when None ✅
- [x] EXECUTE: `scheduler.py` — creates fresh RiskManager at each session wakeup ✅
- [x] EXECUTE: `telegram_client.py` — `send_order_confirmation()` and `send_order_failure()` ✅
- [x] EXECUTE: `requirements.txt` — added `py-clob-client>=0.16.0` ✅
- [x] EXECUTE: `.env.example` — CLOB credential keys added, stale Odds API entry removed ✅

### Verification
- [x] Koyeb deployment healthy — "Smart Scheduler Started 🚀" and discovery confirmed ✅
- [ ] VERIFY: First live bet placed and confirmed on Polymarket — pending next signal
- [ ] VERIFY: Budget cap enforced — bot refuses to bet beyond $5/session

---

## Session 17c — Hotfix: Invalid Token ID (First Hypothesis)
- [x] THINK: Initial hypothesis — markets at ≥97¢ have CLOB trading suspended; Gamma clobTokenIds rejected ✅
- [x] EXECUTE: Add `MAX_WIN_PROB_THRESHOLD = 0.97` to `config.py` ✅
- [x] EXECUTE: Update `scanner.py` filter to `WIN_PROB_THRESHOLD <= prob < MAX_WIN_PROB_THRESHOLD` ✅
- [x] EXECUTE: Update `main.py` to silently log (not Telegram alert) when `Invalid token id` is caught ✅
- [x] VERIFY: Hypothesis refuted — same error at 80.0¢ (Werder Bremen win, clearly non-resolved) ✅

---

## Session 17d — Hotfix: True Root Cause — Gamma clobTokenIds Unreliable ✅
- [x] THINK: True root cause confirmed — Gamma's `clobTokenIds` field is NOT the authoritative CLOB trading token. The CLOB's own `GET /markets/{condition_id}` public endpoint is the correct source ✅
- [x] THINK: Evidence: 80¢ main market + 83¢ O/U 1.5 + 92¢ Spread all failed identically. Probability irrelevant. Token format mismatch is the cause ✅
- [x] EXECUTE: Add `get_clob_yes_token_id(condition_id)` to `polymarket_client.py` — hits `GET /clob.polymarket.com/markets/{condition_id}`, extracts YES token ✅
- [x] EXECUTE: Add `condition_id` (best market's conditionId) to opportunity dict in `scanner.py` ✅
- [x] EXECUTE: Update `main.py` — resolve authoritative token_id from CLOB API before placing order; Gamma's value is fallback only ✅
- [x] VERIFY: `side="BUY"` confirmed working — order fully constructed and sent ✅
- [x] VERIFY: CLOB token_id lookup confirmed working — `Invalid token id` errors gone ✅
- [x] VERIFY: New blocker — `403 Geoblock` — Koyeb's server region is blocked by Polymarket CLOB ✅

---

## Session 17e — Deployment: Resolve Geoblock ✅
- [x] THINK: All Koyeb regions blocked — Frankfurt (Germany, fully blocked), Singapore (close-only), Washington DC (US, blocked) ✅
- [x] THINK: Solution — Fly.io `gru` (São Paulo, Brazil). Brazil not on Polymarket blocked list. ~$2.20/month ✅
- [x] EXECUTE: Create `fly.toml` — shared-cpu-1x 256MB, port 8000, `auto_stop_machines="off"`, `min_machines_running=1`, region `gru` ✅
- [x] EXECUTE: `fly apps create minutebid-gru`, `fly secrets set` (all 6 creds), `fly deploy` ✅
- [x] EXECUTE: Scale to 1 machine (`fly scale count 1`) — remove HA second machine ✅
- [x] EXECUTE: Update UptimeRobot monitor URL → `https://minutebid-gru.fly.dev/` ✅
- [x] EXECUTE: Retire Koyeb service (Singapore) ✅
- [x] VERIFY: `curl -I https://minutebid-gru.fly.dev/` → `200 OK` from `gru` ✅
- [x] VERIFY: Scheduler running — 45 matches discovered, heartbeat every 10 min ✅
- [ ] VERIFY: First `✅ BET PLACED` on Telegram — pending next live match signal

---

## Session 18b — Hotfix: Silence "no match" ORDER FAILED Telegram spam
- [x] THINK: Root cause — `no match` raised by py-clob-client when order book has zero asks (illiquid sub-markets like More Markets spreads); client-side, no HTTP request made ✅
- [x] EXECUTE: Add `err_str == "no match"` to silent-log branch in `main.py` exception handler (alongside existing "Invalid token id" guard) ✅
- [x] VERIFY: Confirmed live — Dortmund vs Bayern O/U 1.5 at 90¢ fired BET SIGNAL; no ORDER FAILED Telegram spam; silently logged as expected ✅
- [ ] VERIFY: First `✅ BET PLACED` on Telegram — pending next *liquid win/draw market* signal (More Markets O/U are illiquid; credentials 401 fix still unverified)
- [ ] OBSERVE: Duplicate BET SIGNAL alerts sent when same opportunity persists across 2 scan cycles (120s apart) — alerts not deduplicated; only bets are (RiskManager); planned fix in Session 19

---

## Session 19 — Moneyline-Only Filter ✅
- [x] THINK: Root cause — Gamma returns Player Props, Total Corners, Halftime Result, Exact Score, More Markets as separate events; old `_SCHEDULE_SUFFIXES` only deduplicated known suffixes, new variants passed through; dashboard showed 41 games vs ~8 actual matches ✅
- [x] EXECUTE: Replace `_base_match_title()` + `_SCHEDULE_SUFFIXES` with `_moneyline_base_title()` in `polymarket_client.py`; returns `None` for any " - " suffix that is not "- Winner" ✅
- [x] EXECUTE: Apply filter in `add_events()` (scanner) and `find_matches()` (scheduler) ✅
- [x] EXECUTE: Update `HANDOFF.md`, `implementation_plan.md`, `MEMORY.md`, `todo.md` ✅
- [x] VERIFY: Committed and pushed to `main` (3171fe8) ✅
- [ ] VERIFY: Dashboard count reduced (expected ~8 matches per day vs previous ~41) — pending next discovery cycle

---

## Session 19b — Credential Debugging & Redeploy ✅
- [x] THINK: Root cause — CLOB 401 persisted because CLOB_PK was set to wallet ADDRESS (20 bytes / 40 chars) instead of private key (32 bytes / 64 chars); Trust Wallet exports PK with `0x` prefix which must be stripped ✅
- [x] EXECUTE: Verify correct CLOB_PK via `Account.from_key()` diagnostic — confirmed `0x06F877...` ✅
- [x] EXECUTE: Update `.env` with correct 64-char Trust Wallet private key (no `0x` prefix) ✅
- [x] EXECUTE: Push all 4 CLOB credentials to Fly.io via `fly secrets set`; machine restarted ✅
- [x] EXECUTE: Update `HANDOFF.md` with Debugging Lesson 7 (CLOB 401 — wallet mismatch + 0x prefix) ✅
- [ ] VERIFY: First `✅ BET PLACED` — pending next liquid win/draw signal

---

## Session 20 — Observability & Post-Bet Analysis (planned)
- [ ] THINK: Log per-bet record (token_id, stake, fill price, P&L) to a persistent file
- [ ] THINK: Session summary Telegram message after each game window closes
- [ ] THINK: Distinguish FOK-cancelled vs filled from order response `status` field
- [ ] THINK: Silence repeated ORDER FAILED spam for auth/infra errors — record failed token_ids to prevent retries within same session
- [ ] THINK: Deduplicate BET SIGNAL alerts — skip Telegram if same token_id alerted within same session window
