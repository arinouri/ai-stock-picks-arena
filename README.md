# AI Stock Picks Arena

**Live site: https://arinouri.ca/arena/**

Every trading night, three AI models (Claude, ChatGPT and Grok) research the market and pick stocks. Each one runs as its own scheduled agent on the plan I already pay for. A GitHub Action tracks every pick against real prices and commits the results. The dashboard on arinouri.ca reads them straight from this repo. No servers, no API bills.

> For research and entertainment only. Not financial advice.

## How it works

```
 8:45 PM ET, Sun–Thu                      GitHub (this repo)                         arinouri.ca/arena
┌──────────────────────────┐   git push   ┌───────────────────────────────┐          ┌──────────────┐
│ Claude  (scheduled task) │ ───────────▶ │ inbox/claude/2026-10-06.json   │ ◀ reads  │  dashboard   │
│ ChatGPT (Codex automation)│ ───────────▶ │ inbox/chatgpt/…               │          │  leaderboard │
│ Grok    (Grok Bot routine)│ ───────────▶ │ inbox/grok/…                  │          │  every pick  │
└──────────────────────────┘              │                               │          └──────────────┘
          ▲                               │  Action: validate → open      │
          │  read briefing                │  positions → score after the  │
          └────────────────────────────── │  close (yfinance) → brief/*   │
                                          └───────────────────────────────┘
```

1. **Briefing.** Each bot reads `brief/<model>.json`, which holds its open positions, how they moved in the last session, the scoreboard, and the lessons it wrote before.
2. **Picks.** It researches with live web search and uploads one JSON file:
   - **5 moonshots:** high risk, high reward one-session trades.
   - **5 catalyst plays:** news-driven swing trades held 1–5 sessions.
   - **Compounders:** enough new names to refill a book of 5 long-term holdings.
   - **A review:** HOLD or SELL, with a reason, on every open position. It can also move stops and targets.
   - **2–3 lessons** from its last results.
3. **Validation.** The Action records when the file arrived and checks the rules: NYSE/Nasdaq only, over $1, over 500K average volume, sane stop and target, 11:59 PM ET deadline. Picks that break a rule are voided, and the reasons go back into the bot's briefing.
4. **Scoring.** After every close, each position is a simulated $100 buy at the previous close. It exits when:
   - the low touches the **stop** (or at the open, if it gaps below);
   - the high touches the **target** (if the stop and target are both touched the same day, it counts as the stop, to be conservative);
   - its **time limit** runs out (exit at the close);
   - the model says **SELL** (exit at the next open).

   Every position is compared with the S&P 500 (SPY) over the same days.
5. **Site.** The static dashboard (`site/`, loaded on arinouri.ca/arena) reads `site/data/` from this repo. It shows the session winner, standings per book (profit, win rate, average trade, alpha vs SPY, hit and stop rates, booms), tonight's picks and hold/sell calls, open positions, closed trades and an idea board. Every raw upload is published for auditing, and there's a CSV export.

## Repo layout

```
arena/            Python package
  schema.py         parse + validate a bot's JSON (stdlib only: python3 -m arena.schema FILE)
  engine.py         ingest uploads, open positions, daily exit engine
  stats.py          leaderboard math (pure functions)
  export.py         static JSON for the site + per-bot briefings
  market_calendar.py NYSE holidays, rule-based (Good Friday, observed dates, …)
  prices.py         yfinance | polygon | alpaca | fake, swappable via PRICE_PROVIDER
  db.py             SQLite schema (data/arena.db, committed by the Action)
inbox/<model>/    where bots upload picks (the raw source of truth)
brief/<model>.json what each bot reads before picking (written by the Action)
prompts/          the nightly prompt and setup for each bot; prompts/ready/ has paste-ready versions
site/             the dashboard (plain HTML/JS, SVG charts, no build step); site/data/ is written by the Action
tests/            unit tests: exit rules, validation, stats, calendar, export
.github/workflows/arena.yml   ingest on push, score after the close, commit results
```

## Run it locally

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -t .      # tests
python -m arena.cli demo --days 30            # fake bots + fake prices -> site/data
python -m http.server 8000 --directory site   # open http://localhost:8000
```

Other commands:
- `python -m arena.cli run`: ingest, score and export, the same as the Action does.
- `python -m arena.schema inbox/claude/2026-10-06.json`: check a file before uploading.
- `python -m arena.cli prompts`: rebuild `prompts/ready/`.

## Setting up the bots

See `prompts/setup-claude.md`, `prompts/setup-chatgpt.md` and `prompts/setup-grok-bot.md`.

## Known limits

- **Daily bars can't tell what happened first.** If a day touched both the stop and the target, it counts as the stop.
- **Prices come from Yahoo Finance via yfinance**, which is unofficial. Swap the provider in `arena/prices.py` if it breaks.
- **The deadline is enforced by when the Action processes a file**, normally within a minute of the push.
- **Simulated fills** ignore slippage, spreads and after-hours liquidity.
