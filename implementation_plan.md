# Minutebid — Implementation Plan

## Goal
A manually-triggered Python script that scans soccer markets. It uses a **"Slow Pulse" strategy**: waking up at Minute 80, checking every 2 minutes, and surfacing outcomes where bookmaker odds hit a "Statistically Resolved" threshold (e.g., < 1.05), implying high confidence in the final result.

---

## Modules

| File | Responsibility | Status |
|------|---------------|--------|
| `config.py` | All constants, thresholds, API base URLs | ✅ Done |
| `polymarket_client.py` | Gamma API + CLOB API HTTP calls | ✅ Done |
| `sports_ws.py` | Polymarket Sports WebSocket → live game minute/score | ✅ Done |
| `scanner.py` | Pure filter: 75-90 min + Polymarket price >= 80% | ✅ Done |
| `display.py` | Terminal table output | ✅ Done |
| `main.py` | Entry point — orchestrates one scan | ✅ Done |
| `scheduler.py` | Long-running loop: discovery, wakeup, active scan sessions | ✅ Done |
| `requirements.txt` | Dependencies | ✅ Done |
| `.env.example` | Credential template | ✅ Done |
| `telegram_client.py` | Telegram alerts and heartbeats | ✅ Done |
| `Dockerfile` | Container definition for cloud deployment | ✅ Done |
| `.dockerignore` | Excludes secrets and artifacts from Docker image | ✅ Done |

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

### Phase 15 — Add UEFA Europa League (UEL) ✅
- Added `'europa_league': 'uel'` to `LEAGUE_TAG_SLUGS` in `config.py`.
- UEL now included in daily discovery alongside UCL, Bundesliga, EPL, La Liga, and Serie A.

### Phase 14 — Cloud Deployment (Koyeb) ✅
- Moved from local Windows machine to Koyeb free tier (always-on Linux container).
- Service type: **Worker** (background process, no HTTP endpoint required).
- Added `Dockerfile` using `python:3.12-slim` with `PYTHONUNBUFFERED=1` for real-time log streaming.
- Added `.dockerignore` to exclude `.env`, logs, and `__pycache__` from the image.
- Added `import platform` guard to `scheduler.py` so `SetThreadExecutionState` is a no-op on Linux.
- Credentials (`ODDS_API_KEY`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`) set as env vars in Koyeb UI — `python-dotenv` reads OS env vars transparently when no `.env` file is present.

---

## Data Flow

```mermaid
graph TD
    A[scheduler.py] -->|1hr loop| B(Gamma API Discovery)
    A -->|Wakeup| C(main.py)
    C -->|Fetch| D[Gamma/Odds/WS APIs]
    D --> E{Scanner Filter}
    E -->|Success| F[Telegram Alert]
    E -->|Display| G[Terminal UI]
```

---

## Key Constraints
- Read-only — no order placement
- No polling loop — one scan per manual run
- Credentials: `ODDS_API_KEY` in `.env`, never in code
- All network calls: 10s timeout, fail gracefully with log

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
