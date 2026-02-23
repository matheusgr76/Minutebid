# Minutebid — Developer Handoff

## Role split
- **Architect (Claude/Gemini Pro):** designed architecture, made API decisions, wrote all modules
- **Developer (Gemini Flash):** picks up from here to complete Phase 2 and beyond

---

## Current state — what exists and works

All files are in `c:\Python\Projects\PLYM_Bots\Minutebid\`.

```
config.py             ✅ done (needs Odds API constants added)
polymarket_client.py  ✅ done — Gamma API + CLOB API
sports_ws.py          ✅ done — Polymarket Sports WebSocket
betfair_client.py     ❌ DELETE THIS — replaced by odds_api_client.py
scanner.py            ✅ done (needs Odds API price format update)
display.py            ✅ done
main.py               ✅ done (needs betfair_client import replaced)
requirements.txt      ✅ done
.env.example          ✅ done (needs ODDS_API_KEY added)
.gitignore            ✅ done
```

Import smoke test passes: `python -c "import config; import polymarket_client; ..."` → OK

---

## Your job — Phase 2: Replace betfair_client with odds_api_client

### Step 1 — Delete `betfair_client.py`

### Step 2 — Create `odds_api_client.py`

**API:** [The Odds API v4](https://the-odds-api.com)
**Free tier:** 500 requests/month, no geo-restriction, works from Brazil
**Key env var:** `ODDS_API_KEY` (loaded from `.env` via `python-dotenv`)

**Endpoint to call:**
```
GET https://api.the-odds-api.com/v4/sports/soccer/odds/
    ?apiKey=YOUR_KEY
    &regions=eu
    &markets=h2h
    &oddsFormat=decimal
    &live=true
```

**Key params:**
| Param | Value | Why |
|-------|-------|-----|
| `regions` | `eu` | European books (Pinnacle, bet365) have best soccer liquidity |
| `markets` | `h2h` | Head-to-head = match winner (Home / Draw / Away) |
| `oddsFormat` | `decimal` | Easier to convert to implied probability: `prob = 1 / decimal_odds` |
| `live` | `true` | In-play markets only |

**Example response structure (simplified):**
```json
[
  {
    "id": "abc123",
    "home_team": "Arsenal",
    "away_team": "Chelsea",
    "bookmakers": [
      {
        "key": "pinnacle",
        "markets": [
          {
            "key": "h2h",
            "outcomes": [
              { "name": "Arsenal", "price": 1.12 },
              { "name": "Chelsea", "price": 15.0 },
              { "name": "Draw",    "price": 8.5 }
            ]
          }
        ]
      }
    ]
  }
]
```

**What `odds_api_client.py` must return:**
```python
# dict keyed by NORMALISED event name, value is dict of outcome → implied prob
{
    "arsenal v chelsea": {
        "arsenal": 0.87,
        "chelsea": 0.07,
        "draw":    0.06,
    }
}
```

**Normalisation:** for each bookmaker's h2h market, implied prob = `1 / decimal_price`.
Use the **average across all bookmakers** (or Pinnacle alone if present — it's the sharpest).
Normalise so probabilities sum to 1.0 (divide each by the sum).

**Graceful failure:** if `ODDS_API_KEY` is missing or API call fails, log a warning and return `{}`.
Scanner already handles empty dict — Polymarket prices still shown, edge column shows `—`.

### Step 3 — Update `config.py`

Add at the bottom:
```python
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
ODDS_API_SPORT = "soccer"          # The Odds API sport key for all soccer
ODDS_API_REGIONS = "eu"
ODDS_API_MARKETS = "h2h"
ODDS_API_ODDS_FORMAT = "decimal"
```

### Step 4 — Update `scanner.py`

In `_lookup_reference_prob()` (currently called `_lookup_betfair_prob`):
- Rename to `_lookup_reference_prob`
- Input format is now `{event_name_str: {outcome_name_str: float}}`
- Logic is already correct — just rename the function and its call site

### Step 5 — Update `main.py`

Replace:
```python
import betfair_client
...
betfair_prices = betfair_client.get_live_soccer_betfair_prices()
```
With:
```python
import odds_api_client
...
reference_prices = odds_api_client.get_live_soccer_reference_prices()
```
Update the `scanner.filter_opportunities()` call to pass `reference_prices`.

### Step 6 — Update `scanner.py` call signature

In `filter_opportunities()`, rename param `betfair_prices` → `reference_prices`.
Update the internal call to `_lookup_reference_prob(event, best["outcome"], reference_prices)`.

### Step 7 — Update `.env.example`

Replace Betfair lines with:
```
# Get free key at: https://the-odds-api.com
ODDS_API_KEY=your_key_here
```

---

## Run instructions (after Phase 2 complete)

```powershell
cd c:\Python\Projects\PLYM_Bots\Minutebid
# Copy .env.example to .env and add your ODDS_API_KEY
$env:PYTHONIOENCODING='utf-8'; python main.py
```

Expected output (during a live match in 75-90 min window):
```
╭──────────────────────┬─────┬───────┬─────────┬───────┬──────────┬───────────╮
│ Match                │ Min │ Score │ Leader  │ Poly% │ Ref%     │ Edge      │
├──────────────────────┼─────┼───────┼─────────┼───────┼──────────┼───────────┤
│ Arsenal vs Chelsea   │ 83' │ 2 - 0 │ Arsenal │ 82.1% │ 93.4%    │ +11.3pp ✅│
╰──────────────────────┴─────┴───────┴─────────┴───────┴──────────┴───────────╯
```

Expected when no games qualify:
```
  ⚽  No qualifying matches right now. Try again during 75-90 min.
```

---

## Constraints (non-negotiable per CLAUDE.md)

- One file per response unless multi-file approval given
- All external calls: 10s timeout, fail with log (never crash)
- No hardcoded credentials — credentials from `.env` only
- File length < 300 lines, function length < 50 lines
- `odds_api_client.py`: single responsibility — fetch and return normalised prices only
- After any EXECUTE, provide: What Changed / Why / Risks Introduced / Change Impact

---

## Reference docs

- The Odds API docs: https://the-odds-api.com/liveapi/guides/v4/
- Polymarket Gamma API: https://gamma-api.polymarket.com
- CLOB API: https://clob.polymarket.com
- Sports WebSocket: wss://sports-api.polymarket.com/ws
- Project SOP: `CLAUDE.md` in this folder
