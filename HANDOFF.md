# Minutebid — Project Handoff

> Last updated: Session 18b (2026-02-28)

## What This Is

Minutebid is a live soccer betting bot that monitors Polymarket in the 75–90+ minute window of soccer matches. When a team's win/outcome probability crosses 80¢, the bot alerts via Telegram and places an automatic $1 USDC bet via Polymarket's CLOB API.

---

## Current System Architecture

### Data Sources
- **Polymarket Gamma API** (`gamma-api.polymarket.com`): Event discovery, schedule, and real-time `bestAsk` prices.
- **Polymarket CLOB API** (`clob.polymarket.com`): Authoritative trading token IDs and order placement.

> **Important:** Gamma and CLOB are two different APIs with different data models. Gamma's `clobTokenIds` field is NOT reliable for order placement — always fetch token_id from `GET /clob.polymarket.com/markets/{condition_id}` before betting.

### Modules

| File | Responsibility |
|------|----------------|
| `config.py` | All constants and thresholds — change here, nowhere else |
| `polymarket_client.py` | Gamma API: event fetch, schedule discovery, price extraction. CLOB API: `get_clob_yes_token_id()` |
| `scanner.py` | Pure filter: time-based minute + probability window `[80%, 97%)` |
| `display.py` | Terminal table output |
| `risk_manager.py` | Session-scoped budget cap ($5/session) and duplicate token guard |
| `trader.py` | `place_order(token_id, stake_usdc)` via `py-clob-client`; FOK market orders |
| `telegram_client.py` | Alerts, heartbeats, live dashboard, order confirmations, failure alerts |
| `main.py` | Single scan entry point; alert-only when `risk_manager=None` |
| `scheduler.py` | Long-running loop: discovery (1h), dashboard (10m), scan (120s) |
| `Dockerfile` | `python:3.12-slim`, `PYTHONUNBUFFERED=1`, `CMD python scheduler.py` |

### Deleted Modules (do not restore)
- `sports_ws.py` — Polymarket's sports WebSocket requires a subscription message that was never sent; returned 0 events every time. Replaced by time-based minute from Gamma `startTime`.
- `odds_api_client.py` — The Odds API free tier has no live odds; the `"soccer"` sport key is also invalid. Dropped in Session 15.

---

## Key Business Logic

- **Wakeup**: kickoff + 80 min (`WAKEUP_DELAY_MINUTES`)
- **Active scan window**: 35 min from wakeup (`SESSION_DURATION_MINUTES`)
- **Scan cadence**: every 120s during active window (`SCAN_INTERVAL_SLOW`)
- **Bet trigger**: `80% <= bestAsk < 97%` in minute 75–120
- **Bet size**: $1.00 flat (`BET_STAKE_USD`), hard cap $5.00/session (`MAX_BET_BUDGET_USD`)
- **Estimated minute**: `(now - event.startTime) / 60` — no WebSocket required
- **Leagues**: EPL, La Liga, Serie A (series IDs), Bundesliga, UCL, UEL (tag slugs)

---

## Cloud Deployment

| Item | Value |
|------|-------|
| Platform | Fly.io (~$2.20/month, $25 prepaid credit loaded) |
| App | `minutebid-gru` |
| Region | `gru` (São Paulo, Brazil) — required: Brazil is not geoblocked by Polymarket CLOB |
| URL | `https://minutebid-gru.fly.dev/` |
| Keep-alive | UptimeRobot pings every 5 min (update monitor to minutebid-gru.fly.dev) |
| Health check | `GET /` → 200 OK served by `_HealthHandler` on port 8000 (daemon thread) |
| Deploy | Manual — `fly deploy` from project root (no auto-deploy on push) |
| Credentials | Set via `fly secrets set` — 6 secrets deployed; never in `.env` in production |
| Config | `fly.toml` in project root — 1 machine, shared-cpu-1x 256MB, auto-stop off |
| Previous platform | Koyeb — **RETIRED** — all regions (Frankfurt/Germany, Singapore, Washington DC/US) are blocked or restricted by Polymarket's CLOB geoblock |

---

## Credentials Required

```
TELEGRAM_TOKEN         # Bot token
TELEGRAM_CHAT_ID       # Target chat ID
CLOB_PK                # Wallet private key (hex, no 0x prefix)
CLOB_API_KEY           # Polymarket CLOB API key
CLOB_API_SECRET        # Polymarket CLOB secret
CLOB_API_PASSPHRASE    # Polymarket CLOB passphrase
```

---

## Opportunity Dict Schema

```python
{
    "match":        str,       # event title from Gamma
    "minute":       int,       # estimated minutes since kickoff
    "outcome":      str,       # market question (e.g. "Will Arsenal win?")
    "poly_prob":    float,     # 0.0–1.0 Polymarket implied probability
    "market_url":   str,       # https://polymarket.com/event/<slug>
    "token_id":     str|None,  # YES token from Gamma (fallback only)
    "condition_id": str|None,  # conditionId for CLOB /markets lookup
}
```

---

## Hard-Won Debugging Lessons

These failures cost real time and money. Read before touching anything.

### 1. Gamma `clobTokenIds` ≠ CLOB token_id
**Symptom**: `PolyApiException[status_code=400, error_message={'error': 'Invalid token id'}]` on every bet attempt, across all probability levels (80¢, 83¢, 92¢ — all failed identically).

**Root cause**: Gamma API returns `clobTokenIds` as a reference field. The CLOB trading system uses different token IDs that must be fetched from `GET /clob.polymarket.com/markets/{condition_id}`.

**Fix**: `polymarket_client.get_clob_yes_token_id(condition_id)` — always call this before placing an order. Gamma's value is last-resort fallback only.

**False lead**: First thought it was near-resolved markets (≥97¢). Added `MAX_WIN_PROB_THRESHOLD = 0.97`. Still failed at 80¢. The probability level was irrelevant.

---

### 2. `MarketOrderArgs` requires explicit `side` — `BUY` not importable
**Symptom**: `MarketOrderArgs.__init__() missing 1 required positional argument: 'side'`

**Fix**: `_SIDE_BUY = 0` defined locally in `trader.py`. The `BUY` constant is not exported from `py_clob_client.clob_types` in the installed version. Do not try to import it.

---

### 3. CLOB credentials in Koyeb Secrets vault ≠ env vars
**Symptom**: `WARNING: RiskManager provided but CLOB credentials missing — running alert-only.`

**Root cause**: Koyeb has two sections — **Secrets vault** (stored but NOT exposed as env vars) and **Environment Variables** (directly exposed). Adding credentials to the Secrets vault does nothing unless you reference them explicitly.

**Fix**: Add CLOB credentials directly in the Environment Variables section with the "Secret" toggle enabled for masking.

---

### 4. Koyeb Secrets vs Env Vars vs Koyeb environment variables
Adding credentials to Koyeb's "Secrets" tab is NOT the same as adding them to the "Environment Variables" tab. Only the Environment Variables tab exposes values as `os.getenv()` accessible. The Secrets tab is a vault — values must be explicitly referenced per-service.

---

### 5. `display.py` stale field names crash silently
**Symptom**: Telegram alerts stopped firing completely. Scheduler showed no errors.

**Root cause**: `display.print_results()` referenced old fields (`reference_prob`, `resolved_outcome`, `score`) from a pre-pivot era. `KeyError` inside `print_results()` was caught by the scheduler's `try/except` and swallowed silently — the Telegram alert call never reached.

**Fix**: Any time you change the opportunity dict schema, check `display.py` immediately.

---

### 6. `"no match"` from py-clob-client on illiquid sub-markets
**Symptom**: `[ERROR] main: Order failed for '... - More Markets': no match`. Telegram sends ORDER FAILED noise every 120s.

**Root cause**: `create_market_order()` internally calls `get_order_book(token_id)` to determine fill price. If the order book has **zero asks** (no sellers), py-clob-client raises `Exception("no match")` client-side — no HTTP request is ever made. This consistently hits "More Markets" spread/O-U events which are thinly traded.

**Fix**: Added `err_str == "no match"` to the silent-log exception guard in `main.py` (alongside `"Invalid token id"`). Both are non-actionable — log warning only, no Telegram alert.

**Diagnostic tip**: If you see "no match" but NOT a preceding `httpx: HTTP Request: POST` log line, it's always this case — client-side, pre-request. If you see "no match" WITH an httpx log line, it's a different error from the CLOB server.

---

### 7. Polymarket Sports WebSocket silently returns nothing
**Symptom**: Scanner always found 0 events in the active game window.

**Root cause**: `wss://sports-api.polymarket.com/ws` requires a subscription message after connection. Without it, the server never pushes data. The bot connected and read — and received nothing.

**Fix**: Deleted `sports_ws.py`. Game minute now estimated from `event.startTime + elapsed` — deterministic, no external dependency.

---

## How to Run Locally

```bash
cp .env.example .env
# Fill in TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, CLOB_PK, CLOB_API_KEY, CLOB_API_SECRET, CLOB_API_PASSPHRASE
pip install -r requirements.txt
python scheduler.py       # Full scheduler loop
python main.py            # Single scan, alert-only (no betting)
```

---

## Next Planned Work (Session 19)

- Log per-bet record (token_id, stake, fill price, P&L) to a persistent file
- Session summary Telegram message after each game window closes
- Distinguish FOK-cancelled vs filled from order response `status` field
- Silence auth/infra ORDER FAILED spam (401, 403) — record failed token_ids to prevent retry within same session window (`"no match"` and `"Invalid token id"` are already silenced)

> **Note**: `fly deploy` required to push any code changes live — git push alone does NOT trigger Fly.io rebuild.
