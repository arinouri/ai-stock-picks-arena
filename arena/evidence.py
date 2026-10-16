"""The skeptic: is anyone here actually good, or just lucky?

Built from closed trades only. For every contestant it reports the average return vs the S&P 500 (alpha),
a 95% confidence interval, how likely it is to beat the random Fruit Fly, and how many more trades
are needed before a +1% edge could even be detected. The "execution lab" tests (without changing any
official score) whether the AIs lose money simply because they buy gapped-up stocks at the open.
"""
from __future__ import annotations

import math
import random
from statistics import mean, stdev
from typing import Optional

from . import config

MIN_N = 20
EDGE = 0.01  # the edge we'd care about: +1% per trade


def _alpha(p) -> Optional[float]:
    r, b = p.ret(), p.benchmark_ret()
    return None if r is None or b is None else r - b


def _closed(positions, key):
    return [p for p in positions if p.status == "closed" and p.model_key == key and p.ret() is not None]


def _verdict(n: int, lo: float, hi: float) -> str:
    if n < MIN_N:
        return "Too early to tell"
    if lo > 0:
        return "Beating the market (so far)"
    if hi < 0:
        return "Losing to the market"
    return "Can't tell from luck yet"


def _boot_diff(a: list, b: list, n: int = 2000, seed: int = 7) -> Optional[float]:
    """Chance that the mean of a beats the mean of b, by resampling both."""
    if len(a) < 5 or len(b) < 5:
        return None
    rng = random.Random(seed)
    wins = sum(mean(rng.choices(a, k=len(a))) > mean(rng.choices(b, k=len(b))) for _ in range(n))
    return round(wins / n, 3)


def _stats(ps, fly_alpha) -> dict:
    al = [a for a in (_alpha(p) for p in ps) if a is not None]
    n = len(al)
    out = {"n": n, "avg_alpha": None, "ci_low": None, "ci_high": None, "t": None, "p_beats_fly": None,
           "trades_needed": None, "verdict": _verdict(n, 0, 0)}
    if n < 3:
        return out
    mu, sd = mean(al), stdev(al)
    se = sd / math.sqrt(n) if sd else 0.0
    lo, hi = mu - 1.96 * se, mu + 1.96 * se
    out.update({
        "avg_alpha": round(mu, 4), "ci_low": round(lo, 4), "ci_high": round(hi, 4),
        "t": round(mu / se, 2) if se else None,
        "p_beats_fly": _boot_diff(al, fly_alpha),
        "trades_needed": int((2 * sd / EDGE) ** 2) if sd else None,
        "verdict": _verdict(n, lo, hi),
    })
    return out


def _first_session(p) -> Optional[dict]:
    """What the first session looked like for one trade, if we have the bars."""
    if not (p.entry_price and p.ref_price and p.d1_close and p.d1_open):
        return None
    return {"gap": p.entry_price / p.ref_price - 1, "open_to_close": p.d1_close / p.entry_price - 1}


def _lab(positions) -> dict:
    """Shadow tests on the AIs' picks. These never change the official scores."""
    c2 = 2 * config.COST_PER_SIDE
    rows = [(p, _first_session(p)) for p in positions
            if p.model_key in config.AI_MODELS and p.status == "closed" and p.bucket != "compounder"]
    rows = [(p, f) for p, f in rows if f]
    if not rows:
        return {"n": 0}
    # a limit order at the top of the AI's own entry zone: fills at the open if the open is inside or
    # under the zone, fills at the zone top if the stock trades down to it, and is missed otherwise.
    limit, missed = [], 0
    for p, f in rows:
        zh = p.entry_zone_high
        if not zh:
            continue
        if p.d1_open <= zh:
            fill = p.d1_open
        elif p.d1_low <= zh:
            fill = zh
        else:
            missed += 1
            continue
        limit.append(p.d1_close / fill - 1 - c2)
    buckets = [("opened down 2%+", -1, -0.02), ("opened -2% to 0%", -0.02, 0.0),
               ("opened 0% to +2%", 0.0, 0.02), ("opened up 2%+", 0.02, 9)]
    by_gap = []
    for label, lo, hi in buckets:
        xs = [f["open_to_close"] - c2 for _, f in rows if lo < f["gap"] <= hi]
        by_gap.append({"label": label, "n": len(xs), "avg_open_to_close": round(mean(xs), 4) if xs else None})
    open_ret = [f["open_to_close"] - c2 for _, f in rows]
    return {
        "n": len(rows),
        "buy_at_open": round(mean(open_ret), 4),
        "limit_at_zone": {"n": len(limit), "missed": missed, "avg": round(mean(limit), 4) if limit else None},
        "by_gap": by_gap,
        "note": "First session only, after costs, no stops or targets. Shadow test: the official score still buys at the open.",
    }


def build(positions) -> dict:
    fly = [a for a in (_alpha(p) for p in _closed(positions, "fly")) if a is not None]
    by = {k: _stats(_closed(positions, k), fly) for k in config.MODELS}
    return {
        "by_model": by,
        "lab": _lab(positions),
        "edge_target": EDGE,
        "explain": ("Alpha = a trade's return after costs minus the S&P 500 over the same days. The range is a 95% confidence "
                    "interval: if it includes 0%, luck explains the result. 'Beats Fruit Fly' is the chance the contestant's "
                    "true average beats random picks."),
    }


def to_markdown(ev: dict) -> list[str]:
    pct = lambda v: "n/a" if v is None else f"{v * 100:+.2f}%"
    lines = ["## Is anyone actually good? (the skeptic)", "", ev["explain"], "",
             "| Contestant | Trades | Avg vs S&P | 95% range | Beats random? | Verdict |", "|---|---|---|---|---|---|"]
    for k, s in ev["by_model"].items():
        if not s["n"]:
            continue
        rng = "n/a" if s["ci_low"] is None else f"{pct(s['ci_low'])} to {pct(s['ci_high'])}"
        pb = "n/a" if s["p_beats_fly"] is None else f"{round(s['p_beats_fly'] * 100)}%"
        lines.append(f"| {k} | {s['n']} | {pct(s['avg_alpha'])} | {rng} | {pb} | {s['verdict']} |")
    lab = ev["lab"]
    if lab.get("n"):
        lz = lab["limit_at_zone"]
        lines += ["", "## Execution lab (shadow test, scores unchanged)", "",
                  f"Across {lab['n']} first-session trades by the AIs, buying at the open averaged {pct(lab['buy_at_open'])} "
                  f"by the close. A limit order at the top of the AI's own entry zone would have averaged {pct(lz['avg'])} "
                  f"({lz['n']} fills, {lz['missed']} missed). Chasing gapped-up stocks at the open is where money leaks, "
                  "so set an entry zone you'd actually be happy to buy at, and pass if the stock is likely to open far above it.", "",
                  "| Where the stock opened vs your close | Trades | Avg open-to-close |", "|---|---|---|"]
        lines += [f"| {g['label']} | {g['n']} | {pct(g['avg_open_to_close'])} |" for g in lab["by_gap"]]
    return lines
