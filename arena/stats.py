"""Leaderboard math. Pure functions over plain records so they're easy to test."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Iterable, Optional

from . import config


@dataclass
class Trade:
    id: int
    model: str
    bucket: str
    ticker: str
    first_session: dt.date
    status: str  # open | closed
    ret: Optional[float]
    exit_reason: Optional[str] = None
    sessions_held: int = 0
    bench_ret: Optional[float] = None
    d1: dict = field(default_factory=dict)

    @property
    def pnl(self) -> float:
        return (self.ret or 0.0) * config.NOTIONAL


@dataclass
class Day:
    model: str
    bucket: str
    date: dt.date
    pnl: float
    position_id: int = 0
    ret: float = 0.0  # that session's move for the position


def _avg(v: list[float]) -> Optional[float]:
    return sum(v) / len(v) if v else None


def _rate(n: int, d: int) -> Optional[float]:
    return n / d if d else None


def daily_pnl(days: Iterable[Day]) -> dict[str, dict[dt.date, float]]:
    out: dict[str, dict[dt.date, float]] = {}
    for d in days:
        out.setdefault(d.model, {}).setdefault(d.date, 0.0)
        out[d.model][d.date] += d.pnl
    return out


def session_winners(days: Iterable[Day]) -> dict[dt.date, str]:
    per: dict[dt.date, dict[str, float]] = {}
    for d in days:
        per.setdefault(d.date, {}).setdefault(d.model, 0.0)
        per[d.date][d.model] += d.pnl
    return {date: max(models.items(), key=lambda kv: (kv[1], kv[0]))[0] for date, models in per.items()}


def equity_curve(pnl_by_date: dict[dt.date, float]) -> list[dict]:
    total, out = 0.0, []
    for d in sorted(pnl_by_date):
        total += pnl_by_date[d]
        out.append({"date": d.isoformat(), "pnl": round(total, 2)})
    return out


def board(trades: list[Trade], days: list[Day], models: Iterable[str], bucket: Optional[str] = None,
          since: Optional[dt.date] = None) -> list[dict]:
    """One row per model, ranked by total P&L ($100 per position, realized + open)."""
    if bucket:
        trades = [t for t in trades if t.bucket == bucket]
        days = [d for d in days if d.bucket == bucket]
    if since:
        trades = [t for t in trades if t.first_session >= since]
        keep = {t.id for t in trades}
        days = [d for d in days if d.position_id in keep]
    winners = session_winners(days)
    pnl_days = daily_pnl(days)
    rows = []
    for m in models:
        mine = [t for t in trades if t.model == m and t.ret is not None]
        closed = [t for t in mine if t.status == "closed"]
        d1 = [t.d1 for t in mine if t.d1]
        alpha = [t.ret - t.bench_ret for t in closed if t.bench_ret is not None]
        total = sum(t.pnl for t in mine)
        best = max(mine, key=lambda t: t.ret, default=None)
        worst = min(mine, key=lambda t: t.ret, default=None)
        rows.append({
            "model": m,
            "positions": len(mine),
            "open": len(mine) - len(closed),
            "closed": len(closed),
            "total_pnl": round(total, 2),
            "return_on_capital": _rate(total, config.NOTIONAL * len(mine)),
            "avg_return": _avg([t.ret for t in closed]),
            "win_rate": _rate(sum(t.ret > 0 for t in closed), len(closed)),
            "target_rate": _rate(sum(t.exit_reason == "target" for t in closed), len(closed)),
            "stop_rate": _rate(sum(t.exit_reason == "stop" for t in closed), len(closed)),
            "model_sells": sum(t.exit_reason == "model_sell" for t in closed),
            "avg_alpha": _avg(alpha),
            "avg_hold": _avg([t.sessions_held for t in closed]),
            "booms": sum(1 for x in d1 if x.get("boom")),
            "d1_avg_to_close": _avg([x["pct_to_close"] for x in d1]),
            "d1_target_rate": _rate(sum(1 for x in d1 if x.get("hit_target")), len(d1)),
            "best": _trade_ref(best),
            "worst": _trade_ref(worst),
            "sessions_won": sum(1 for w in winners.values() if w == m),
            "sessions": len(pnl_days.get(m, {})),
            "equity": equity_curve(pnl_days.get(m, {})),
        })
    rows.sort(key=lambda r: (r["positions"] > 0, r["total_pnl"]), reverse=True)
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


def _trade_ref(t: Optional[Trade]) -> Optional[dict]:
    if t is None:
        return None
    return {"id": t.id, "ticker": t.ticker, "bucket": t.bucket, "ret": t.ret, "status": t.status}


def session_summary(days: list[Day], session: dt.date, models: Iterable[str]) -> list[dict]:
    rows = []
    for m in models:
        mine = [d for d in days if d.model == m and d.date == session]
        by_bucket = {b: round(sum(d.pnl for d in mine if d.bucket == b), 2) for b in config.BUCKETS}
        rows.append({"model": m, "pnl": round(sum(d.pnl for d in mine), 2), "by_bucket": by_bucket,
                     "positions": len(mine)})
    rows.sort(key=lambda r: (r["positions"] > 0, r["pnl"]), reverse=True)
    return rows
