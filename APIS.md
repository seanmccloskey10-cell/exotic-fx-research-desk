# API Options — Equity Research Desk

Full directory of financial data APIs she can evaluate. Organized by what problem each one solves. **All crypto APIs deliberately excluded** per user preference.

---

## Already built into the tool

| API | Role | Key needed? | Cost |
|---|---|---|---|
| **yfinance** | Primary data source — quotes, fundamentals, historical, company info | No | Free |
| **Finnhub** | Secondary — news, earnings calendar | Yes (free tier) | Free: 60 calls/min |
| **Alpha Vantage** | Tertiary fallback — fundamentals | Yes (free tier) | Free: 25 calls/day |
| **Anthropic Claude** | AI briefing tab | Yes (budget-capped) | ~$0.05 per briefing |

These ship with the tool. Everything below is optional she can add.

---

## Top 3 next additions (my recommendations)

### 1. Financial Modeling Prep (FMP) — **best value add**
- **Gives her:** deep fundamentals, income statements, balance sheets, cash flows, financial ratios, analyst estimates, insider trading data
- **Free tier:** 250 calls/day
- **Paid:** $19/mo Starter (unlimited fundamentals)
- **Why it matters:** Much deeper fundamental data than Finnhub or Alpha Vantage. Great for real equity research.
- **URL:** https://site.financialmodelingprep.com/
- **Python:** `pip install fmpsdk` or plain `requests`

### 2. FRED (St. Louis Federal Reserve) — **free macro context**
- **Gives her:** interest rates, inflation, GDP, employment, housing, any macro indicator
- **Free tier:** unlimited (just need a free API key)
- **Paid:** N/A — always free
- **Why it matters:** Helps her understand *why* stocks move — Fed decisions, inflation prints, etc.
- **URL:** https://fred.stlouisfed.org/docs/api/fred/
- **Python:** `pip install fredapi`

### 3. Quartr — **earnings call transcripts**
- **Gives her:** full earnings call transcripts, investor presentations
- **Free tier:** limited
- **Paid:** starts ~$20/mo
- **Why it matters:** Earnings transcripts are where real research lives. Much richer than headlines.
- **URL:** https://quartr.com/
- **Note:** This is also available as a **Cowork connector** — if she has Claude Pro/Max, she may be able to use it from Cowork directly without adding it to this tool.

---

## Full directory by category

### Market data (quotes, OHLC, historical)

| API | Free tier | Paid starts | Notes |
|---|---|---|---|
| yfinance | Unlimited (no key) | N/A | Already built in. Yahoo Finance backend. |
| Polygon.io | 5 calls/min, end-of-day only | $29/mo (basic real-time) | Best free tier for historical data. Real-time is paid. |
| Tiingo | 50/hour, 500/day | $10/mo | Clean API, good news feed included. |
| Twelve Data | 800/day, 8/min | $29/mo | Covers forex too if she ever wants that. |
| EODHD | 20 calls/day (demo) | $19.99/mo | End-of-day focus, deep history. |
| Marketstack | 100 calls/month | $9.99/mo | Simple API, limited free tier. |
| Finage | 500 calls/day | $17/mo | Good Python SDK. |
| Intrinio | Trial only | $100+/mo | Enterprise-grade, expensive. |

### News & sentiment

| API | Free tier | Paid starts | Notes |
|---|---|---|---|
| Finnhub News | 60/min | $0 | Already integrated. |
| NewsAPI.org | 100/day (dev) | $449/mo (commercial) | Broad news, not finance-specific. |
| Mediastack | 500/month | $9.99/mo | News aggregator. |
| Benzinga News | Trial | $177/mo | Finance-specific, signals + news. |
| Stocktwits API | Free read access (limits apply) | Business plans | Social sentiment / retail chatter. |
| Reddit (PRAW) | Free | N/A | r/wallstreetbets / r/stocks for retail signal. |
| Seeking Alpha | Limited RSS | Paid content behind login | Best equity analysis content but hard to integrate. |

### Fundamentals & ratios

| API | Free tier | Paid starts | Notes |
|---|---|---|---|
| Financial Modeling Prep | 250/day | $19/mo | **Recommended** — deep statements + ratios. |
| Alpha Vantage | 25/day | $49.99/mo | Already integrated as fallback. |
| Intrinio | Trial | $100+/mo | Best-in-class fundamentals, pricey. |
| Quandl / Nasdaq Data Link | Some free datasets | Varies by dataset | Academic focus, dataset-by-dataset pricing. |

### Macro / economic data

| API | Free tier | Paid starts | Notes |
|---|---|---|---|
| **FRED (St. Louis Fed)** | Unlimited (needs free key) | N/A | **Recommended** — Fed data, gold standard for macro. |
| World Bank Open Data | Unlimited | N/A | Country-level economic data. |
| OECD Stats | Unlimited | N/A | International economic indicators. |
| Trading Economics | Limited | $25/mo | All-in-one macro. |
| EIA (US Energy Info) | Unlimited | N/A | Energy prices, production. Useful for commodity-correlated FX (CAD, NOK, AUD). |

### Earnings & calendar

| API | Free tier | Paid starts | Notes |
|---|---|---|---|
| Finnhub Earnings | 60/min | $0 | Already integrated. |
| FMP Earnings | 250/day | $19/mo | Richer earnings estimates. |
| Quartr | Limited | ~$20/mo | **Transcripts.** Best-in-class. |
| Aiera | Contact sales | Enterprise | Live earnings call transcription + AI. Cowork connector available. |
| Earnings Whispers | Paid | ~$10/mo | Whisper estimates (retail expectations vs. consensus). |

### Analyst estimates

| API | Free tier | Paid starts | Notes |
|---|---|---|---|
| Finnhub Recommendations | Free | $0 | Already integrated (via Finnhub). |
| FMP Analyst Estimates | 250/day | $19/mo | Good coverage. |
| Estimize | Research license only | Enterprise | Crowdsourced estimates. |
| Refinitiv I/B/E/S | Enterprise only | $$$$ | Gold standard, not accessible to retail. |

### Options data

| API | Free tier | Paid starts | Notes |
|---|---|---|---|
| Polygon Options | 5/min | $29/mo | Chain data, Greeks. |
| Tradier | Brokerage account | $10/mo data | Free with brokerage account. |
| CBOE DataShop | None | Per-dataset pricing | Authoritative source. |
| Barchart OnDemand | Trial | Enterprise | Professional-grade. |

### SEC filings & official documents

| API | Free tier | Paid starts | Notes |
|---|---|---|---|
| **SEC EDGAR** | Unlimited, no key | N/A | **Recommended** — source of truth for 10-K, 10-Q, 8-K, insider trading. |
| EDGAR Online (paid) | N/A | Enterprise | Pre-processed filings. |
| Intrinio SEC | Trial | $100+/mo | Normalized filing data. |

### Insider trading & institutional holdings

| API | Free tier | Paid starts | Notes |
|---|---|---|---|
| Finnhub Insider | Free | $0 | Basic coverage. |
| FMP Insider | 250/day | $19/mo | Form 4 filings. |
| Whale Wisdom | Free basic | $20+/mo | 13F institutional holdings. |
| Quiver Quantitative | Limited | $10/mo | Congressional trading, government contracts, patents. |

### Alternative / thematic

| API | Free tier | Paid starts | Notes |
|---|---|---|---|
| TradingView | N/A (charts embed only) | $14.95+/mo for API | Excellent charting if she ever wants embedded charts. |
| Koyfin | Web app, no API | $35/mo | **Not an API — web dashboard.** If she wants the "no-code" path instead of building, this is the consumer-grade answer. Worth knowing about. |
| ESG Book | Contact sales | Enterprise | Sustainability / ESG scores. |
| Visible Alpha | Enterprise | $$$$ | Analyst consensus detail. |
| YCharts | Trial | $79/mo | Chartbook with decent data feed. |

---

## Decision framework — how to evaluate a new API

When she considers adding one, her agent should walk her through these questions:

1. **What specific data does this give me that I don't already have?**
2. **Is the free tier enough for my usage pattern?** (She's running briefings maybe daily/weekly — hundreds of calls/day would be wildly over-provisioned for her.)
3. **What's the paid tier trigger?** (e.g. "I'd only pay for this if I wanted real-time data for day-trading" — she doesn't, so free tier is fine.)
4. **Does this overlap with Cowork's built-in connectors?** (Cowork has Morningstar, S&P, LSEG, Moody's, Aiera, Quartr, Fiscal.ai — if a connector covers it, use Cowork instead.)
5. **How easy is the Python integration?** (Official Python SDK > REST with documented endpoints > poorly-documented API.)

---

## Quick recommendation matrix for the user

| Her question | Best free pick | Best paid pick (under $25/mo) |
|---|---|---|
| "I want deeper fundamentals" | FMP (250/day) | FMP Starter $19/mo |
| "I want macro context" | **FRED** (unlimited) | — stays free |
| "I want earnings transcripts" | Quartr limited tier, or use Cowork connector | Quartr ~$20/mo |
| "I want better news" | Already have Finnhub; RSS from Seeking Alpha | Tiingo $10/mo |
| "I want options data" | Polygon free (5/min) | Polygon Starter $29/mo |
| "I want SEC filings" | **SEC EDGAR** (unlimited, free) | — stays free |
| "I want ESG data" | ESG Book (contact) | Premium only — skip |
| "I just want pretty charts without building" | (N/A) | **Koyfin $35/mo** (not an API, a web app) |

---

## How to add a new API to this tool

She says to her agent:
> "I want to add [API name]. My key is: [paste key]. Please wire it into the `data_sources/` folder following the pattern of the existing sources, and add an entry to the fallback cascade in `data_sources/orchestrator.py`."

Her agent will:
1. Create `data_sources/<name>_source.py` implementing the `DataSource` base class
2. Add the key to `.env` and document it in `.env.example`
3. Register the source in the orchestrator
4. Test a call
5. Report back

She doesn't need to touch any code herself. See `CLAUDE.md` for the exact pattern the agent follows.

---

## What's NOT in this list

- **Any crypto APIs** (user preference)
- **Broker APIs** (Alpaca, IBKR, etc.) — out of scope; this is a research tool, not a trading platform
- **Backtest platforms** (QuantConnect, etc.) — different product category
- **Streaming / real-time data feeds** (beyond what Polygon offers at $29/mo) — not needed for weekly research workflow
- **Bloomberg Terminal / FactSet / Refinitiv** — enterprise pricing ($1k+/mo), not realistic for hobby use
