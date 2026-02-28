# Minutebid — Implementation Plan

## Goal
A manually-triggered Python script that scans soccer markets. It uses a **"Slow Pulse" strategy**: waking up at Minute 80, checking every 2 minutes, and surfacing outcomes where bookmaker odds hit a "Statistically Resolved" threshold (e.g., < 1.05), implying high confidence in the final result.

---

## Modules

| File | Responsibility | Status |
|------|---------------|--------|
| `config.py` | All constants, thresholds, API base URLs | ✅ Done |
| `polymarket_client.py` | Gamma API fetching, schedule discovery, price extraction | ✅ Done |
| `scanner.py` | Pure filter: time-based minute + Polymarket price >= 80% | ✅ Done |
| `display.py` | Terminal table output | ✅ Done |
| `main.py` | Entry point — orchestrates one scan | ✅ Done |
| `scheduler.py` | Long-running loop: discovery, wakeup, active scan sessions | ✅ Done |
| `requirements.txt` | Dependencies | ✅ Done |
| `.env.example` | Credential template | ✅ Done |
| `telegram_client.py` | Telegram alerts and heartbeats | ✅ Done |
| `Dockerfile` | Container definition for cloud deployment | ✅ Done |
| `.dockerignore` | Excludes secrets and artifacts from Docker image | ✅ Done |
| `risk_manager.py` | Budget cap, per-bet stake sizing, duplicate guard | ✅ Session 17 |
| `trader.py` | CLOB order placement via `py-clob-client` | ✅ Session 17 |

---

## Phases

### Phase 1 — Core Scaffold ✅
All modules wired, imports verified, dependencies installed.

### Phase 2 — Reference Price Source ✅
- Delete `betfair_client.py`
- Write `odds_api_client.py` using [The Odds API](https://the-odds-api.com)
- Update `config.py` with Odds API settings
- Update `scanner.py` for Odds API price format
- Update `.env.example` with `ODDS_API_KEY`
- Update `requirements.txt`
- Update `requirements.txt` (remove betfair-specific notes)

### Phase 5 — Smart Bot Scheduling ✅
- Added `polymarket_client.get_soccer_schedule()` for discovery.
- Created `scheduler.py` with 95-minute wakeup logic.
- Refactored `main.py` for session-based scanning.

### Phase 6 — Telegram Notifications ✅
- Send real-time alerts for discovered opportunities and bot heartbeats.
- Created `telegram_client.py` using Telegram Bot API.
- Integrated alerts into `main.py` and `scheduler.py`.
- Added credential templates to `.env.example`.

### Phase 7 — Fuzzy Team Name Matching ✅
- Improved matching reliability between Polymarket (Gamma) and Odds API.
- Implemented `rapidfuzz.token_set_ratio` to handle variations like "Arsenal FC" vs "Arsenal".
- Added automated normalization for common soccer suffixes.

### Phase 8 — Enhanced Scheduler Monitoring ✅
- Implemented `update_scheduler_dashboard` in `telegram_client.py`: sends/edits a single live message with T-minus countdowns, capped at 15 games to respect Telegram's 4096-char limit.
- Dashboard update throttled to every 300s (5 min).

### Phase 9 — Slow Pulse Monitoring (Strategic Pivot) ✅
- Reduced scan frequency to **120 seconds** (2 minutes).
- Pivoted from "Edge Hunting" to "Consensus Following" using bookmaker odds threshold.

### Phase 13 — Scanner Pivot: Polymarket-Only ✅
- Root cause: `ODDS_API_SPORT = "soccer"` is not a valid The Odds API key; free tier also has no live odds → scanner never fired a single bet alert.
- Dropped The Odds API entirely. `odds_api_client.py` deleted.
- Scanner now alerts on Polymarket price alone: any outcome >= `WIN_PROB_THRESHOLD` (80%) in the 75–90+ min window triggers a bet signal.
- Removed dead constants from `config.py` (`ODDS_API_*`, `RESOLVED_ODDS_THRESHOLD`, `MIN_EDGE_THRESHOLD`).
- `ODDS_API_KEY` credential no longer required.

### Phase 17 — Automatic Betting via CLOB ✅
- **Trigger**: manual signal capture too slow; live signals confirmed correct; waived 2-3 week observation prerequisite.
- **New modules**: `risk_manager.py` (session-scoped budget cap + duplicate guard), `trader.py` (py-clob-client wrapper, FOK market orders).
- **Key fix in `scanner.py`**: added `token_id` field (`clobTokenIds[0]`) to opportunity dict — previously missing, order placement would have been impossible.
- **Signal flow**: scanner → Telegram alert → `risk_manager.approve()` → `trader.place_order()` → `risk_manager.record_bet()` → Telegram confirmation / failure alert.
- **Graceful degradation**: if CLOB credentials absent, bot continues in alert-only mode (no crash).
- **Budget**: `MAX_BET_BUDGET_USD = $5.00` per session, `BET_STAKE_USD = $1.00` flat stake.
- **Order type**: FOK (Fill or Kill) — immediate fill or cancelled; no stale orders after game ends.
- **Credentials added**: `CLOB_PK`, `CLOB_API_KEY`, `CLOB_API_SECRET`, `CLOB_API_PASSPHRASE`.
- **Branch**: `feature/automatic-betting` — pending review before merge to main.

### Phase 16b — Fix: display.py Silent Crash on Bet Signal ✅
- Root cause: `display.print_results()` still referenced old Odds API era fields (`reference_prob`, `resolved_outcome`, `score`). Any real opportunity caused a `KeyError`, which the scheduler's `try/except` swallowed silently — Telegram alert was never sent.
- Fix: updated `display.py` print loop to use current scanner output fields: `outcome` and `poly_prob`.
- Impact: this bug was present since the Session 15 Polymarket-only pivot. Every real signal in that window was silently discarded before reaching Telegram.

### Phase 16 — Drop WebSocket, Time-Based Minute Detection ✅
- Root cause: `wss://sports-api.polymarket.com/ws` returns 0 events every scan — the API requires a subscription message that was never sent. Scanner always skipped every game silently.
- Fix: deleted `sports_ws.py` entirely. `scanner.py` now calculates game minute as `(now - kickoff) / 60` using the event's `startTime` from the Gamma API.
- `main.py`: removed `sports_ws` import and `get_live_game_states()` call.
- `telegram_client.py`: removed score line; minute shown as `~82` to indicate estimated value.
- Net result: scanner is deterministic, no external WebSocket dependency, alerts will fire correctly in the 75–90+ min window.

### Phase 15 — Add UEFA Europa League (UEL) ✅
- Added `'europa_league': 'uel'` to `LEAGUE_TAG_SLUGS` in `config.py`.
- UEL now included in daily discovery alongside UCL, Bundesliga, EPL, La Liga, and Serie A.

### Phase 14 — Cloud Deployment (Koyeb) ✅
- Moved from local Windows machine to Koyeb free tier (always-on Linux container).
- Service type: **Worker** (background process, no HTTP endpoint required).
- Added `Dockerfile` using `python:3.12-slim` with `PYTHONUNBUFFERED=1` for real-time log streaming.
- Added `.dockerignore` to exclude `.env`, logs, and `__pycache__` from the image.
- Added `import platform` guard to `scheduler.py` so `SetThreadExecutionState` is a no-op on Linux.
- Credentials (`TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `CLOB_PK`, `CLOB_API_KEY`, `CLOB_API_SECRET`, `CLOB_API_PASSPHRASE`) set as Secrets in Koyeb UI — `python-dotenv` reads OS env vars transparently when no `.env` file is present.

---

## Data Flow (current — Session 17)

```mermaid
graph TD
    A[scheduler.py] -->|1hr loop| B(Gamma API Discovery)
    A -->|Wakeup at kickoff+80min| C(main.py + RiskManager)
    C -->|get_active_soccer_events| D[Gamma API]
    D --> E{scanner.filter_opportunities}
    E -->|minute from startTime + elapsed| E
    E -->|prob >= 80% in min 75-120| F[Telegram Alert]
    F --> G{risk_manager.approve}
    G -->|ok| H[trader.place_order FOK]
    G -->|duplicate / budget| I[skip silently]
    H -->|filled| J[Telegram: BET PLACED]
    H -->|failed| K[Telegram: ORDER FAILED]
```

## Data Flow (Session 17 — Automatic Betting — archived diagram)

```mermaid
graph TD
    A[scanner finds opportunity] --> B{risk_manager}
    B -->|budget ok, not duplicate| C[trader.place_order]
    B -->|budget exceeded| D[Telegram: budget warning]
    C -->|order filled| E[Telegram: BET PLACED]
    C -->|order failed| F[Telegram: order failure alert]
```

---

## Key Constraints
- Credentials: never hardcoded, always in env vars
- All network calls: 10s timeout, fail gracefully with log
- Budget hard cap: `MAX_BET_BUDGET_USD` enforced before every order
- No duplicate bets: same market cannot be bet twice in one session

---
























# ADDITIONAL FEATURES

## Phase 5 - Smart Daily Scheduler (Quota Aware)

### [Component] Orchestration (Scheduling)
#### [NEW] [scheduler.py](file:///c:/Python/Projects/PLYM_Bots/Minutebid/scheduler.py)
- **Discovery Mode**: On manual daily start, fetch all soccer matches starting T+24h.
- **Wakeup Logic**: Calculate `start_time + 75 minutes` and sleep until that window opens.
- **Active Scanning**: Once in the window, use WebSocket to track live minute. Trigger scan only during `75-90+`.

#### [MODIFY] [main.py](file:///c:/Python/Projects/PLYM_Bots/Minutebid/main.py)
- Refactor scanning logic to be callable as `run_scan(event_ids)` for specific targeted events.

### [Component] Configuration
#### [MODIFY] [config.py](file:///c:/Python/Projects/PLYM_Bots/Minutebid/config.py)
- Add discovery thresholds and scheduling constants.

## Phase 8 - Scheduler UI (Telegram) ✅

### [Component] Telegram Client
#### [DONE] [telegram_client.py](file:///c:/Python/Projects/PLYM_Bots/Minutebid/telegram_client.py)
- `update_scheduler_dashboard(runs)`: sends or edits a single live Telegram message with T-minus countdowns. Capped at 15 games. Persists message ID to `.dashboard_msg_id` for in-place edits.

### [Component] Orchestration
#### [DONE] [scheduler.py](file:///c:/Python/Projects/PLYM_Bots/Minutebid/scheduler.py)
- Dashboard update throttled to 300s interval via `last_dashboard_update` tracker.
- Discovery (1h), dashboard (5m), and scan (15s) cycles are fully independent.

## Verification Plan

### Manual Verification
- Run discovery and confirm the list of "Today's Games" is accurate.
- Verify the bot sleeps/wakes correctly during a simulated match window.
- Monitor Odds API call logs to ensure zero waste.

---

## Future Development — Phase 16: Automatic Betting

### Overview
Once the bot proves profitable through manual observation, Minutebid can be extended to place bets automatically using a fixed budget (e.g. $10 USD) with no manual intervention per signal.

### How It Works
Polymarket exposes a CLOB (Central Limit Order Book) API that supports programmatic order placement. The official `py-clob-client` Python SDK handles cryptographic signing and order building.

### New Components Required

| File | Role |
|------|------|
| `trader.py` | New module: `place_order(token_id, stake_usdc)` via `py-clob-client` |
| `risk_manager.py` | New module: budget cap, per-bet stake, duplicate-market guard |
| `config.py` | Add `MAX_BET_BUDGET_USD`, `BET_STAKE_USD`, `CLOB_API_KEY`, `CLOB_API_SECRET` |
| `main.py` | Wire opportunity → risk_manager → trader |
| `telegram_client.py` | Add `send_order_confirmation()` alert |
| `.env.example` | Add `CLOB_API_KEY`, `CLOB_API_SECRET` |

### Signal Flow (new)
```
scanner finds opportunity
  → risk_manager approves stake size
  → trader.place_order(token_id, stake_usdc)
  → Telegram: "✅ BET PLACED: $1.00 on Arsenal @ 87¢"
```

### Prerequisites Before Building
1. ~~2–3 weeks of live signal monitoring~~ — **waived**: multiple live signals confirmed correct; manual execution too slow to capture opportunities in time
2. ~~Polymarket account~~ — **ready** ✅
3. Fund Polymarket account with USDC on Polygon
4. Generate CLOB API credentials in Polymarket UI
5. Decide on staking strategy (flat stake recommended first)

### Key Risks
- **Key exposure**: private key in Koyeb env vars (same pattern as TELEGRAM_TOKEN — acceptable)
- **Runaway bets**: scanner bug fires many signals → `MAX_BET_BUDGET_USD` hard cap prevents overspend
- **Slippage**: market orders near 87¢ may fill worse; check `bestAsk` before committing
- **CLOB downtime**: order silently fails → must alert on failure via Telegram
