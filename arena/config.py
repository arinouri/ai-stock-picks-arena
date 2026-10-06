"""Contest rules and settings. Everything a bot needs to know is also published in its briefing."""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Contestants. The key is also the inbox folder name: inbox/<key>/<YYYY-MM-DD>.json
MODELS = {
    "claude": {"display_name": "Claude", "maker": "Anthropic", "color": "#C2410C"},
    "chatgpt": {"display_name": "ChatGPT", "maker": "OpenAI", "color": "#0F8A6A"},
    "grok": {"display_name": "Grok", "maker": "xAI", "color": "#4F5BD5"},
}

# The three books every model runs
BUCKETS = {
    "moonshot": {
        "label": "Moonshots",
        "about": "High risk, high reward. One-session trades on stocks that could rip tomorrow.",
        "new_per_night": 5,
        "horizon": (1, 1),
        "default_horizon": 1,
        "max_open": None,
    },
    "catalyst": {
        "label": "Catalyst plays",
        "about": "Research-driven swing trades on current news: earnings, FDA, deals, upgrades. Held 1–5 sessions.",
        "new_per_night": 5,
        "horizon": (1, 5),
        "default_horizon": 3,
        "max_open": None,
    },
    "compounder": {
        "label": "Compounders",
        "about": "A standing book of up to 5 quality stocks held for weeks to months. Only replace names when there's a reason.",
        "new_per_night": None,  # however many it takes to fill the book back up to max_open
        "horizon": (10, 120),
        "default_horizon": 60,
        "max_open": 5,
    },
}

NOTIONAL = 100.0  # every position is a simulated $100 buy, so dollar P&L is comparable across models
BOOM_THRESHOLD = 0.10  # first-session high at least +10% from entry
MIN_PRICE = 1.0
MIN_AVG_VOLUME = 500_000
SUBMISSION_DEADLINE = dt.time(23, 59)  # ET, on the night the picks are made
VOID_AFTER_MISSING_SESSIONS = 5  # no price data this many sessions in a row -> position voided
BENCHMARK = "SPY"

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{ROOT / 'data' / 'arena.db'}")
INBOX_DIR = Path(os.getenv("ARENA_INBOX", ROOT / "inbox"))
SITE_DIR = Path(os.getenv("ARENA_SITE", ROOT / "site"))
PRICE_PROVIDER = os.getenv("PRICE_PROVIDER", "yfinance")
REPO = os.getenv("GITHUB_REPOSITORY", "arinouri/ai-stock-picks-arena")
SITE_URL = os.getenv("ARENA_SITE_URL", f"https://{REPO.split('/')[0]}.github.io/{REPO.split('/')[1]}")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")
ALPACA_API_KEY_ID = os.getenv("ALPACA_API_KEY_ID", "")
ALPACA_API_SECRET = os.getenv("ALPACA_API_SECRET", "")
