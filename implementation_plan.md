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

### Phase 3 — Verification
- Smoke test: confirm imports and live API calls work without auth errors
- Live end-to-end: run during a match window and inspect output
- Cross-check: verify one displayed opportunity matches Polymarket UI manually

### Phase 4 — Hardening (future session, if needed)
- Retry logic on HTTP failures (exponential back-off)
- Tighter event name matching between Polymarket ↔ Odds API
- Unit tests for `scanner.filter_opportunities()` with synthetic data
- Optional: `--dry-run` flag, `--threshold` override at CLI

---

## Data Flow

```
[Gamma API]  →  active soccer events
[CLOB API]   →  YES token prices (Polymarket implied prob)
[Sports WS]  →  live game minute + score
[Odds API]   →  reference prices from major books
     ↓
[scanner.py]  →  filter (min, prob, edge)
     ↓
[display.py]  →  terminal table
```

---

## Key Constraints
- Read-only — no order placement
- No polling loop — one scan per manual run
- Credentials: `ODDS_API_KEY` in `.env`, never in code
- All network calls: 10s timeout, fail gracefully with log
