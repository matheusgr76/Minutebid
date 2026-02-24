# Minutebid — Implementation Plan

## Goal
A manually-triggered Python script that scans Polymarket for live soccer markets in minutes 75–90+, surfaces outcomes with >80% implied win probability, and cross-references The Odds API to detect mispriced opportunities (edge).

---

## Modules

| File | Responsibility | Status |
|------|---------------|--------|
| `config.py` | All constants, thresholds, API base URLs | ✅ Done — needs Odds API constants |
| `polymarket_client.py` | Gamma API + CLOB API HTTP calls | ✅ Done |
| `sports_ws.py` | Polymarket Sports WebSocket → live game minute/score | ✅ Done |
| `odds_api_client.py` | The Odds API → reference prices from major bookmakers | 🔄 Replacing `betfair_client.py` |
| `scanner.py` | Pure filter: 75-90 min + >80% prob + edge calc | ✅ Done — needs Odds API format update |
| `display.py` | Terminal table output | ✅ Done |
| `main.py` | Entry point — orchestrates one scan | ✅ Done |
| `requirements.txt` | Dependencies | ✅ Done — needs `betfair_client` removed |
| `.env.example` | Credential template | ✅ Done — needs Odds API key |

---

## Phases

### Phase 1 — Core Scaffold ✅
All modules wired, imports verified, dependencies installed.

### Phase 2 — Reference Price Source 🔄 (current)
- Delete `betfair_client.py`
- Write `odds_api_client.py` using [The Odds API](https://the-odds-api.com)
  - Endpoint: `GET /v4/sports/soccer/odds` with `inPlay=true`
  - Returns: best back prices from multiple bookmakers (Pinnacle, bet365, etc.)
  - Requires: free API key (500 req/month free tier)
- Update `config.py` with Odds API base URL and key env var name
- Update `scanner.py` for Odds API price format (bookmaker → outcome → price)
- Update `.env.example` with `ODDS_API_KEY`
- Update `requirements.txt` (remove betfair-specific notes)

### Phase 5 — Smart Bot Scheduling ✅
- Added `polymarket_client.get_soccer_schedule()` for discovery.
- Created `scheduler.py` with 95-minute wakeup logic.
- Refactored `main.py` for session-based scanning.

### Phase 6 — Telegram Notifications (Proposed)
- **Goal**: Send real-time alerts for discovered opportunities and bot heartbeats.
- [NEW] `telegram_client.py`: Implementation using `requests` to call Telegram Bot API.
- [MODIFY] `main.py`: Call `telegram_client` when opportunities are discovered.
- [MODIFY] `scheduler.py`: Send "Bot Started" and "Sleeping" status updates.
- [MODIFY] `.env`: Add `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID`.

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

## Verification Plan

### Manual Verification
- Run discovery and confirm the list of "Today's Games" is accurate.
- Verify the bot sleeps/wakes correctly during a simulated match window.
- Monitor Odds API call logs to ensure zero waste.
