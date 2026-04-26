# Prompts — what to say to your agent

Copy any line below, paste it to your Claude Code agent in VS Code, and hit Enter. Your agent reads this file and knows the patterns.

---

## Getting started

- *"Clone this repo and get it running for me: https://github.com/seanmccloskey10-cell/equity-research-desk"*
  — Your agent follows README's **Bootstrap** section: checks for Python 3.11+ and Git (installs via `brew` on macOS, or `winget` on Windows, if missing), clones the repo, runs `python3 run.py setup` (macOS) or `python run.py setup` (Windows), then the matching `start` command. Dashboard opens at http://localhost:8501.
- *"I want to use this equity research tool — can you set it up?"*
- *"Check if the setup is working and let me know what I need to do next."*
  — Your agent runs `python3 run.py setup` (macOS) / `python run.py setup` (Windows) and reports back.

## Using the dashboard

- *"Start the dashboard."*
- *"Stop the dashboard."*
- *"Refresh the data."*
- *"Open the dashboard in my browser."*
- *"Is the dashboard still running?"*

## Managing the watchlist

- *"Add TSLA to my watchlist."*
- *"Remove USDPHP from my watchlist."*
- *"What stocks am I tracking right now?"*
- *"Replace USDIDR with USDKRW in my watchlist."*
- *"Reset my watchlist to the original five tickers."*

## Adding API keys

- *"Help me add my Finnhub API key to the project."*
- *"Help me add my Alpha Vantage API key to the project."*
- *"Help me add my Claude API key so I can get AI briefings."*
- *"Check which API keys I currently have set up."*

## AI Briefing

- *"Generate an AI briefing for me."*
  — Opens the briefing tab; you click the button yourself (the confirmation dialog is on purpose, to prevent surprise costs).
- *"Download today's briefing as a markdown file."*
  — Use the ⬇ Download .md button inside the briefing panel.
- *"Show me my briefing history."*
  — List files in `briefings/` directory.
- *"Delete the briefing from <date>."*
- *"What's in the briefing prompt template?"*
  — Agent reads `config/briefing_prompt.md`.
- *"Change the briefing prompt to focus more on risks."*
  — Agent edits `config/briefing_prompt.md`.

## Budget & safety (Anthropic / Claude API)

- *"What's my Claude API budget this month?"*
  — Agent reads `briefings/.usage.jsonl` and sums the current month.
- *"How much have I spent on briefings this year?"*
- *"Raise my Anthropic monthly budget to $10. Explain the tradeoff first."*
- *"Lower the minimum time between briefings to 30 minutes."*
- *"Disable AI briefings for this month."* (empties `ANTHROPIC_API_KEY`)
- *"Reset my usage ledger."* (agent should push back — see TROUBLESHOOTING.md)

## Customizing views (Phase 2+)

- *"Change the default timeframe on the Detail view to 3 months."*
- *"Show the highest-P/E stocks first in the overview table."*
  — Or just click the P/E column header in the table.
- *"Add a sector column to the overview table."*
- *"Hide the Volume column from Overview."*

## Troubleshooting

- *"The dashboard isn't loading. Figure out what's wrong."*
  — Agent reads TROUBLESHOOTING.md and runs diagnostic commands.
- *"My Finnhub key isn't being recognized. Help me debug."*
- *"Why is the news section empty?"*
- *"The price for USDTRY looks wrong — investigate."*
- *"Port 8501 is already in use. What do I do?"*
- *"The AI briefing button is greyed out — why?"*
- *"I get a `.env.txt` error. Fix it for me."*

## Make it yours — customization prompts

The tool is yours. These are three things you can ask your agent to change that will make the dashboard feel like you designed it. Each is a single-file edit, visibly different afterwards, and low-risk.

### 1. Change the accent color (aesthetic)

Browse <https://mobbin.com/colors/brand> and pick a brand palette you love — or just a single hex code that matches your mood. Then paste:

> *"Change my dashboard's accent color to `#EF4444` (that's an example — swap in whatever hex I give you). Edit `config/theme.py`'s `COLORS['accent']` and `COLORS['accent_soft']` (pick a lighter shade of the same hue for the soft variant). Show me the diff before saving so I can see what's changing."*

The accent color drives: the page-header underline on every tab, active-tab highlights, sidebar tick marks, metric-card hover borders, button outlines, link colors in the AI Brief, and the gradient on the TL;DR hero card. Anything "blue" in the current look becomes whatever you pick. Change takes effect on next page refresh.

### 2. Add a "YTD %" column to the Overview table (functional)

> *"Add a 'YTD %' column to the Overview table, right after the 'Day %' column. Color-code the same way — green for positive, red for negative, tabular numerics so the column lines up. The helper `_ytd_pct()` already exists in `views/overview.py` so you just need to call it for each ticker and add it to the `column_config` block. Show me the result."*

Gives you "how has each stock done this year" at a glance, alongside the intraday move. Already-implemented helper → low-risk table extension.

### 3. Personalize the AI Brief's tone (content)

> *"Make my AI Brief more personal. At the top of `config/briefing_prompt.md`, have it open by addressing me as the user, and in the 'Watchlist snapshot' section have it lead with my 5-stock portfolio before the broader market context (currently the other way round). Keep all the accuracy rules exactly as they are — just change the voice and the ordering. Show me the diff before saving."*

The briefing template is plain markdown with no code — your agent can edit the system prompt and user prompt sections freely. Change applies the next time you click "Generate Briefing" (cached briefings stay cached; regenerate to see the new style).

---

## Extending the tool (bigger changes)

- *"Add a new tab that shows dividend history for each stock."*
- *"Add Alpha Vantage as a data source for earnings dates."*
- *"Create a separate watchlist for ETFs, distinct from my individual stocks."*
- *"Add a currency toggle so I can see prices in AED as well as USD."*
- *"Add Financial Modeling Prep as a data source."* (see APIS.md for the API directory)

## Learning the codebase (for when the user is curious)

- *"Walk me through how a price appears on screen — from yfinance to the dashboard."*
- *"Explain how the data source cascade works, in plain English."*
- *"Show me the file I'd edit to change the dashboard's color scheme."*
- *"Explain why the Settings tab is read-only."* (§5.6 budget protection story)
- *"How does the AI briefing avoid burning through my API credits?"* (ten-item §5.6 answer)

---

**Tip.** If something above doesn't work the way it reads, tell your agent what you expected — it will diagnose and fix. This file grows as your tool grows.
