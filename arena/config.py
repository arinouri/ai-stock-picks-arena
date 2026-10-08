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
    # Built-in contestants that run inside the GitHub Action (no inbox):
    "learner": {"display_name": "The Learner", "maker": "Reinforcement learning agent", "color": "#B4237A"},
    "fly": {"display_name": "Fruit Fly", "maker": "Random picks (control group)", "color": "#7C7F87"},
}
AI_MODELS = ("claude", "chatgpt", "grok")  # the ones that upload files
AGENT_MODELS = ("learner", "fly")

# The Learner: picks this many of the AIs' picks each night (those it expects to beat the S&P 500)
LEARNER_PICKS_PER_NIGHT = 5
LEARNER_PRIOR_PRECISION = 4.0  # how strongly weights are pulled toward 0 before there's evidence
LEARNER_NOISE_SD = 0.06  # assumed spread of a single trade's return vs the S&P 500
# The Fruit Fly: same books as the AIs, random tickers, fixed exits
FLY_RULES = {
    "moonshot": {"n": 5, "target": 0.10, "stop": 0.05, "horizon": 1},
    "catalyst": {"n": 5, "target": 0.12, "stop": 0.06, "horizon": 3},
    "compounder": {"n": None, "target": 0.30, "stop": 0.15, "horizon": 60},
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
# Picks are made after the close, so the earliest anyone could act on them is the next session's open.
# Every position is bought at that open. Trading isn't free: each side costs this much (spread + slippage).
COST_PER_SIDE = 0.001  # 0.10% in, 0.10% out
LEARNER_HALF_LIFE_DAYS = 90  # the Learner trusts a trade's lesson half as much after this many days
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
SITE_URL = os.getenv("ARENA_SITE_URL", "https://arinouri.ca/arena/")
RAW_URL = f"https://raw.githubusercontent.com/{REPO}/main"
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")
ALPACA_API_KEY_ID = os.getenv("ALPACA_API_KEY_ID", "")
ALPACA_API_SECRET = os.getenv("ALPACA_API_SECRET", "")
