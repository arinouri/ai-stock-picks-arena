"""Fixed-capital portfolio accounting and professional performance statistics.

This is deliberately separate from the arena's original $100-per-pick score. Every
contestant starts with the same cash, uses the same position size, and cannot spend
cash twice. Results are reconstructed from immutable entries and daily marks, so no
new production tables or historical rewrites are required.
"""
from __future__ import annotations

import datetime as dt
import math
import statistics
from collections import defaultdict
from typing import Iterable, Optional

from . import config
from .db import Benchmark, Position


def _finite(values: Iterable[Optional[float]]) -> list[float]:
    return [float(v) for v in values if v is not None and math.isfinite(float(v))]


def _drawdown(curve: list[dict], initial: Optional[float] = None) -> tuple[Optional[float], list[dict]]:
    peak, worst, out = initial, 0.0, []
    for row in curve:
        equity = row["equity"]
        peak = equity if peak is None else max(peak, equity)
        dd = equity / peak - 1 if peak else 0.0
        worst = min(worst, dd)
        out.append({"date": row["date"], "drawdown": dd})
    return (worst if curve else None), out


def _daily_returns(curve: list[dict]) -> list[float]:
    return [curve[i]["equity"] / curve[i - 1]["equity"] - 1 for i in range(1, len(curve))
            if curve[i - 1]["equity"] > 0]


def _risk_metrics(curve: list[dict], closed_returns: list[float], initial: Optional[float] = None) -> dict:
    daily = _daily_returns(curve)
    mean = statistics.fmean(daily) if daily else None
    vol = statistics.stdev(daily) if len(daily) >= 2 else None
    downside = [min(0.0, r) for r in daily]
    downside_dev = statistics.stdev(downside) if len(downside) >= 2 else None
    years = len(daily) / 252
    base = initial if initial is not None else (curve[0]["equity"] if curve else None)
    total = curve[-1]["equity"] / base - 1 if curve and base else None
    gains = sum(r for r in closed_returns if r > 0)
    losses = -sum(r for r in closed_returns if r < 0)
    max_dd, drawdowns = _drawdown(curve, initial)
    enough_daily = len(daily) >= 20
    return {
        "total_return": total,
        "annualized_return": ((1 + total) ** (1 / years) - 1
                              if total is not None and total > -1 and years >= 0.25 else None),
        "volatility": vol * math.sqrt(252) if enough_daily and vol is not None else None,
        "sharpe": mean / vol * math.sqrt(252) if enough_daily and vol not in (None, 0) else None,
        "sortino": mean / downside_dev * math.sqrt(252)
        if enough_daily and downside_dev not in (None, 0) else None,
        "max_drawdown": max_dd,
        "median_trade_return": statistics.median(closed_returns) if closed_returns else None,
        "profit_factor": gains / losses if losses > 0 else (None if gains == 0 else None),
        "daily_observations": len(daily),
        "sample_warning": ("Fewer than 20 daily observations; annualized risk ratios are unavailable."
                           if len(daily) < 20 else None),
        "drawdown": drawdowns,
    }


def simulate_model(positions: list[Position], benchmarks: list[Benchmark], model: str) -> dict:
    """Rebuild one contestant's fixed-capital account in chronological order.

    Existing positions are admitted by session, then rank and id. A buy consumes a
    fixed 5% of starting capital including entry costs. Open slots and settled cash
    are hard constraints. Same-day exits become cash only after that day's entries,
    a conservative convention when daily bars cannot establish intraday ordering.
    """
    initial = config.PORTFOLIO_INITIAL_CAPITAL
    target = initial * config.PORTFOLIO_POSITION_FRACTION
    mine = [p for p in positions if p.model_key == model and p.entry_price and p.days and p.status != "void"]
    by_entry: dict[dt.date, list[Position]] = defaultdict(list)
    marks: dict[dt.date, dict[int, float]] = defaultdict(dict)
    exits: dict[dt.date, list[Position]] = defaultdict(list)
    all_days = set()
    for p in mine:
        by_entry[p.first_session].append(p)
        for day in p.days:
            marks[day.date][p.id] = day.mark
            all_days.add(day.date)
        if p.exit_date and p.status == "closed":
            exits[p.exit_date].append(p)
    if not all_days:
        return {"model": model, "initial_capital": initial, "equity": [], "drawdown": [],
                "metrics": {**_risk_metrics([], [], initial), "cash": initial, "open_positions": 0,
                            "completed_trades": 0, "skipped_for_capital": 0}}

    cash = initial
    holdings: dict[int, dict] = {}
    closed_returns: list[float] = []
    costs = 0.0
    skipped = 0
    curve = []
    first, last = min(all_days), max(all_days)
    bench_by_date = {b.date: b for b in benchmarks}
    bench_start = next((bench_by_date[d].open or bench_by_date[d].close for d in sorted(bench_by_date) if d >= first), None)
    bench_curve = []

    for day in sorted(all_days):
        # Capital released today is intentionally unavailable to today's new entries.
        for p in sorted(by_entry.get(day, []), key=lambda p: (p.rank, p.id)):
            if len(holdings) >= config.PORTFOLIO_MAX_OPEN or cash + 1e-9 < target:
                skipped += 1
                continue
            fee = target * config.COST_PER_SIDE / (1 + config.COST_PER_SIDE)
            shares = target / ((1 + config.COST_PER_SIDE) * p.entry_price)
            cash -= target
            costs += fee
            holdings[p.id] = {"position": p, "shares": shares, "cost": target,
                              "last": p.entry_price, "entry_fee": fee}

        for pid, mark in marks.get(day, {}).items():
            if pid in holdings:
                holdings[pid]["last"] = mark

        for p in sorted(exits.get(day, []), key=lambda p: p.id):
            h = holdings.pop(p.id, None)
            if h is None:
                continue
            gross = h["shares"] * p.exit_price
            exit_fee = gross * config.COST_PER_SIDE
            proceeds = gross - exit_fee
            cash += proceeds
            costs += exit_fee
            closed_returns.append(proceeds / h["cost"] - 1)

        market_value = sum(h["shares"] * h["last"] * (1 - config.COST_PER_SIDE) for h in holdings.values())
        equity = cash + market_value
        curve.append({"date": day.isoformat(), "equity": round(equity, 2),
                      "cash": round(cash, 2), "invested": round(market_value, 2),
                      "open_positions": len(holdings)})
        b = bench_by_date.get(day)
        if b and bench_start:
            bench_curve.append({"date": day.isoformat(), "equity": round(initial * b.close / bench_start, 2)})

    metrics = _risk_metrics(curve, closed_returns, initial)
    metrics.update({
        "cash": round(cash, 2),
        "open_positions": len(holdings),
        "completed_trades": len(closed_returns),
        "skipped_for_capital": skipped,
        "transaction_costs": round(costs, 2),
        "exposure": statistics.fmean(r["invested"] / r["equity"] for r in curve if r["equity"] > 0),
        "turnover": (len(closed_returns) * target + sum(h["cost"] for h in holdings.values())) / initial,
        "benchmark_return": (bench_curve[-1]["equity"] / initial - 1) if bench_curve else None,
    })
    metrics["alpha_vs_spy"] = (metrics["total_return"] - metrics["benchmark_return"]
                                if metrics["total_return"] is not None and metrics["benchmark_return"] is not None
                                else None)
    return {"model": model, "initial_capital": initial, "position_size": target,
            "max_open": config.PORTFOLIO_MAX_OPEN, "equity": curve,
            "drawdown": metrics.pop("drawdown"), "benchmark": bench_curve, "metrics": metrics}


def simulate_all(positions: list[Position], benchmarks: list[Benchmark], models: Iterable[str]) -> dict:
    return {model: simulate_model(positions, benchmarks, model) for model in models}
