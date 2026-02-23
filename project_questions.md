# Minutebid — Project Decisions Log

## Validated Assumptions

| # | Assumption | Status | Resolution |
|---|-----------|--------|------------|
| A1 | Polymarket has live in-play soccer markets with real-time pricing | ✅ Confirmed | User confirmed prices update in real-time during matches |
| A2 | YES token mid-price = implied win probability | ✅ Confirmed | Standard prediction market interpretation |
| A3 | Sports WebSocket provides game minute reliably | ✅ Acceptable | `sports_ws.py` connects, reads batch, returns empty dict gracefully on failure |
| A4 | Soccer is filterable by tag on the Gamma API | ✅ Confirmed | Tag ID discovered dynamically via `/sports` endpoint each run |

---

## Key Decisions Made

### 1. Source of truth for reference prices: The Odds API
- **Rejected:** Betfair Exchange API — blocked for Brazilian accounts as of Jan 1, 2025
- **Chosen:** [The Odds API](https://the-odds-api.com) — public REST API, works from Brazil, free tier (500 req/month), aggregates Pinnacle + bet365 + others
- **Credential required:** `ODDS_API_KEY` in `.env` (get free key at the-odds-api.com)

### 2. Module name: `odds_api_client.py` (not `betfair_client.py`)
- File `betfair_client.py` exists but must be **deleted**
- Replacement: `odds_api_client.py`
- Function to call: `get_live_soccer_reference_prices()` → returns `{event_name: {outcome: prob}}`

### 3. Edge detection is the core value-add
- Goal is not just finding >80% Polymarket markets — it's finding markets where **The Odds API also agrees but Polymarket is underpricing** (positive edge)
- Edge = `reference_prob - poly_prob`; flagged ✅ if ≥ 5pp (configurable via `MIN_EDGE_THRESHOLD` in `config.py`)

### 4. Filters
- Match minute: **75–90+ min** (configurable: `MIN_MINUTE`, `MAX_MINUTE` in `config.py`)
- Win probability threshold: **>80%** (configurable: `WIN_PROB_THRESHOLD` in `config.py`)
- Period: second half only (checked against `period` field from Sports WebSocket)

### 5. Scope: read-only
- No auto-betting, no order placement in this version
- Output is a terminal table; user decides manually

---

## Architecture Summary

```
main.py
  ├── polymarket_client.py  → Gamma API (events) + CLOB API (prices)
  ├── sports_ws.py          → Polymarket Sports WebSocket (game minute, score)
  ├── odds_api_client.py    → The Odds API live in-play reference prices  ← Phase 2
  ├── scanner.py            → filter logic (pure function, no I/O)
  └── display.py            → terminal table output
```

---

## Open items for Session 2

- [ ] Obtain `ODDS_API_KEY` at https://the-odds-api.com and add to `.env`
- [ ] Gemini Flash to implement Phase 2 per `HANDOFF.md`
- [ ] Run live end-to-end test during a match window (75-90 min)
