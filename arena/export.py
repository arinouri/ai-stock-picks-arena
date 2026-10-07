"""Write the static site's data files (site/data/*) and the per-bot briefings."""
from __future__ import annotations

import csv
import datetime as dt
import io
import json
import shutil
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from . import config
from .db import AIModel, Benchmark, Position, PositionDay, Review, Submission
from .engine import ACTIVE, ET, last_closed_session, now_et
from .market_calendar import next_trading_day, session_plan, should_run_picks_tonight
from .stats import Day, Trade, board, session_summary

EXAMPLE_SUBMISSION = {
    "model": "claude",
    "model_version": "the exact model name you are running as, if you know it",
    "market_view": "One or two sentences on the market going into tomorrow.",
    "lessons": ["2-3 short lessons from your last results (read them in your briefing)"],
    "review": [
        {"position_id": 123, "ticker": "ABC", "action": "HOLD", "reason": "Thesis intact; raising stop to lock gains.",
         "new_stop": 41.5, "new_target": None},
        {"position_id": 124, "ticker": "XYZ", "action": "SELL", "reason": "Guidance cut removes the catalyst."},
    ],
    "moonshot": [
        {"ticker": "ABC", "thesis": "Reports after the close tonight; options imply a 14% move and short interest is 22%.",
         "catalyst_time": "2026-10-06 after close", "entry_zone_low": 40.1, "entry_zone_high": 41.0,
         "target_price": 46.0, "stop_price": 37.5, "confidence": "medium",
         "main_risk": "A beat with weak guidance gets sold.", "sources": ["https://..."]},
    ],
    "catalyst": [
        {"ticker": "DEF", "thesis": "...", "catalyst_time": "...", "target_price": 0, "stop_price": 0,
         "horizon_days": 3, "confidence": "high", "main_risk": "...", "sources": ["https://..."]},
    ],
    "compounder": [
        {"ticker": "GHI", "thesis": "...", "target_price": 0, "stop_price": 0, "horizon_days": 60,
         "confidence": "high", "main_risk": "...", "sources": ["https://..."]},
    ],
}

RULES = {
    "notional": f"Every position is a simulated ${config.NOTIONAL:.0f} buy at the reference price.",
    "reference_price": "The regular-session close of the day you make the picks (Friday's close on Sunday night).",
    "exits": [
        "Stop: if the session's low touches your stop you're out at the stop (or at the open if it gaps below).",
        "Target: if the high touches your target you're out at the target (or at the open if it gaps above).",
        "Both in one session counts as the stop.",
        "Time: out at the close when the position has been held horizon_days sessions.",
        "SELL in your review: out at the next session's open.",
    ],
    "eligibility": f"NYSE/Nasdaq only, no OTC, price above ${config.MIN_PRICE:.0f}, 20-day average volume above "
                   f"{config.MIN_AVG_VOLUME // 1000}K, target above and stop below the reference close. "
                   "Picks that break a rule are voided and don't score.",
    "deadline": f"The file must arrive by {config.SUBMISSION_DEADLINE:%H:%M} ET on the night you make the picks. "
                "You can upload again before then; the newest file replaces the old one.",
    "buckets": {k: {"label": v["label"], "about": v["about"], "new_per_night": v["new_per_night"],
                    "horizon_days": list(v["horizon"]), "max_open": v["max_open"]} for k, v in config.BUCKETS.items()},
}


def _d(x: Optional[dt.date]) -> Optional[str]:
    return x.isoformat() if x else None


def serialize_position(p: Position, last_review: Optional[Review] = None, bench_last: Optional[float] = None,
                       intraday: bool = False) -> dict:
    out = {
        "id": p.id, "model": p.model_key, "bucket": p.bucket, "ticker": p.ticker, "thesis": p.thesis,
        "catalyst_time": p.catalyst_time, "sources": p.sources or [], "confidence": p.confidence,
        "main_risk": p.main_risk, "horizon_days": p.horizon_days, "entry_date": _d(p.entry_date),
        "first_session": _d(p.first_session), "entry_price": p.entry_price, "entry_zone": [p.entry_zone_low, p.entry_zone_high],
        "target": p.target, "stop": p.stop, "orig_target": p.orig_target, "orig_stop": p.orig_stop,
        "status": p.status, "last_price": p.last_price, "last_date": _d(p.last_date), "sessions_held": p.sessions_held,
        "exit_date": _d(p.exit_date), "exit_price": p.exit_price, "exit_reason": p.exit_reason,
        "ret": p.ret(), "pnl": round(p.pnl(), 2), "bench_ret": p.benchmark_ret(bench_last), "d1": p.d1(),
        "flags": p.flags or [], "sell_at_open_on": _d(p.sell_at_open_on), "submission_id": p.submission_id,
        "has_intraday": bool(p.d1_intraday),
    }
    if intraday and p.d1_intraday:
        out["intraday"] = p.d1_intraday
    if last_review is not None:
        out["last_review"] = {"action": last_review.action, "reason": last_review.reason,
                              "date": _d(last_review.effective_date)}
    return out


def export_site(db: Session, site_dir: Optional[Path] = None, now: Optional[dt.datetime] = None,
                brief_dir: Optional[Path] = None) -> dict:
    site_dir = site_dir or config.SITE_DIR
    now = (now or now_et()).astimezone(ET)
    data = site_dir / "data"
    if data.exists():
        shutil.rmtree(data)
    for sub in ("models", "raw", "brief"):
        (data / sub).mkdir(parents=True, exist_ok=True)

    models = {m.key: m for m in db.scalars(select(AIModel)).all()}
    keys = [k for k in config.MODELS if k in models]
    positions = db.scalars(select(Position).where(Position.status != "void").options(
        selectinload(Position.days))).all()
    voided = db.scalars(select(Position).where(Position.status == "void")).all()
    subs = db.scalars(select(Submission).order_by(Submission.received_at)).all()
    reviews = db.scalars(select(Review).join(Submission).where(Submission.status.in_(ACTIVE))
                         .order_by(Review.effective_date)).all()
    last_review = {r.position_id: r for r in reviews}
    bench_rows = db.scalars(select(Benchmark).order_by(Benchmark.date)).all()
    bench_last = bench_rows[-1].close if bench_rows else None

    trades = [Trade(id=p.id, model=p.model_key, bucket=p.bucket, ticker=p.ticker, first_session=p.first_session,
                    status=p.status, ret=p.ret(), exit_reason=p.exit_reason, sessions_held=p.sessions_held,
                    bench_ret=p.benchmark_ret(bench_last), d1=p.d1()) for p in positions if p.entry_price]
    days = [Day(model=p.model_key, bucket=p.bucket, date=d.date, pnl=d.pnl, position_id=p.id,
                ret=d.mark / d.prev_mark - 1) for p in positions if p.entry_price for d in p.days]
    last_session = max((d.date for d in days), default=None)
    today = now.date()

    boards = {}
    for window, since in (("all", None), ("30d", today - dt.timedelta(days=30)), ("7d", today - dt.timedelta(days=7))):
        boards[window] = {b or "all": board(trades, days, keys, b, since) for b in [None, *config.BUCKETS]}

    # Latest picks per model (tonight, or the most recent night)
    latest_target = max((s.target_date for s in subs if s.status in ACTIVE), default=None)
    by_sub: dict[int, list[Position]] = {}
    for p in [*positions, *voided]:
        by_sub.setdefault(p.submission_id, []).append(p)
    pos_by_id = {p.id: p for p in positions}

    def serialize_sub(s: Submission, full: bool = False) -> dict:
        out = {"id": s.id, "model": s.model_key, "path": s.path, "run_date": _d(s.run_date),
               "ref_date": _d(s.ref_date), "target_date": _d(s.target_date),
               "received_at": s.received_at.isoformat() + "Z", "status": s.status, "errors": s.errors or [],
               "market_view": s.market_view, "lessons": s.lessons or [], "model_version": s.model_version,
               "picks": [serialize_position(p, last_review.get(p.id), bench_last,
                                            intraday=full and p.first_session == last_session)
                         for p in sorted(by_sub.get(s.id, []), key=lambda p: p.rank)],
               "reviews": [{"position_id": r.position_id, "ticker": pos_by_id[r.position_id].ticker
                            if r.position_id in pos_by_id else "?", "bucket": pos_by_id[r.position_id].bucket
                            if r.position_id in pos_by_id else "", "action": r.action, "reason": r.reason,
                            "new_stop": r.new_stop, "new_target": r.new_target} for r in s.reviews]}
        return out

    latest = {}
    for k in keys:
        mine = [s for s in subs if s.model_key == k and s.target_date == latest_target and s.status != "superseded"]
        latest[k] = serialize_sub(mine[-1], full=True) if mine else None
    previous_session_subs = {}
    if last_session:
        for k in keys:
            mine = [s for s in subs if s.model_key == k and s.target_date == last_session and s.status in ACTIVE]
            previous_session_subs[k] = serialize_sub(mine[-1], full=True) if mine else None

    open_positions = [serialize_position(p, last_review.get(p.id), bench_last) for p in positions if p.status == "open"]
    closed = sorted((p for p in positions if p.status == "closed"), key=lambda p: (p.exit_date, p.id), reverse=True)

    movers = []
    if last_session:
        for d in days:
            if d.date == last_session:
                p = pos_by_id[d.position_id]
                movers.append({"id": p.id, "model": p.model_key, "ticker": p.ticker, "bucket": p.bucket,
                               "ret": d.ret, "pnl": round(d.pnl, 2)})
        movers.sort(key=lambda m: m["ret"], reverse=True)

    run_date = today if now.time() < config.SUBMISSION_DEADLINE else today + dt.timedelta(days=1)
    while not should_run_picks_tonight(run_date):
        run_date += dt.timedelta(days=1)
    next_night = {"run_date": run_date.isoformat(), "session": session_plan(run_date)[1].isoformat(),
                  "deadline": f"{run_date} {config.SUBMISSION_DEADLINE:%H:%M} ET"}

    meta = {"generated_at": now.isoformat(), "last_session": _d(last_session),
            "last_closed_session": last_closed_session(now).isoformat(), "next_night": next_night,
            "repo": config.REPO, "site_url": config.SITE_URL, "notional": config.NOTIONAL,
            "buckets": RULES["buckets"],
            "models": [{"key": k, "display_name": models[k].display_name, "maker": models[k].maker,
                        "color": models[k].color} for k in keys]}

    dashboard = {
        "meta": meta,
        "session": {"date": _d(last_session),
                    "standings": session_summary(days, last_session, keys) if last_session else [],
                    "movers": movers[:5], "losers": movers[-3:][::-1] if len(movers) > 5 else [],
                    "picks": previous_session_subs},
        "boards": boards,
        "latest": {"target_date": _d(latest_target), "submissions": latest},
        "open": open_positions,
        "closed": [serialize_position(p, last_review.get(p.id), bench_last) for p in closed[:80]],
        "ideas": [{"model": s.model_key, "date": _d(s.run_date), "market_view": s.market_view, "lessons": s.lessons}
                  for s in reversed(subs) if s.status in ACTIVE and (s.lessons or s.market_view)][:24],
        "inbox": [{"model": s.model_key, "path": s.path, "status": s.status, "received_at": s.received_at.isoformat() + "Z",
                   "errors": (s.errors or [])[:6]} for s in reversed(subs)][:20],
        "benchmark": [{"date": _d(b.date), "close": b.close} for b in bench_rows[-260:]],
    }
    _write(data / "dashboard.json", dashboard)

    for k in keys:
        mine = [s for s in subs if s.model_key == k]
        _write(data / "models" / f"{k}.json", {
            "model": k, "submissions": [serialize_sub(s) for s in reversed(mine)],
            "positions": [serialize_position(p, last_review.get(p.id), bench_last)
                          for p in sorted(positions, key=lambda p: p.id, reverse=True) if p.model_key == k]})
        brief = briefing(k, models[k], positions, last_review, mine, boards, days, last_session, next_night, bench_last)
        _write(data / "brief" / f"{k}.json", brief)
        if brief_dir is not None:  # also committed to the repo so git-based bots can read it after a pull
            brief_dir.mkdir(parents=True, exist_ok=True)
            (brief_dir / f"{k}.json").write_text(json.dumps(brief, indent=1, default=str), encoding="utf-8")
    for s in subs:
        (data / "raw" / f"{s.id}.txt").write_text(
            f"model: {s.model_key}\nfile: {s.path}\nreceived (UTC): {s.received_at}\nstatus: {s.status}\n"
            f"problems: {json.dumps(s.errors or [])}\n\n{s.raw}", encoding="utf-8")
    (data / "export.csv").write_text(export_csv(positions, voided, bench_last), encoding="utf-8")
    return {"positions": len(positions), "submissions": len(subs), "last_session": _d(last_session)}


def _pick_nights(start: dt.date, n: int) -> list[dict]:
    out, d = [], start
    while len(out) < n:
        if should_run_picks_tonight(d):
            out.append({"run_date": d.isoformat(), "session": session_plan(d)[1].isoformat()})
        d += dt.timedelta(days=1)
    return out


def briefing(key, model, positions, last_review, subs, boards, days, last_session, next_night, bench_last) -> dict:
    mine_open = [p for p in positions if p.model_key == key and p.status == "open"]
    comp_open = sum(1 for p in mine_open if p.bucket == "compounder")
    last_sub = subs[-1] if subs else None
    recent_lessons = []
    for s in reversed(subs):
        if s.status in ACTIVE and s.lessons:
            recent_lessons += s.lessons
        if len(recent_lessons) >= 6:
            break
    last_results = []
    if last_session:
        for p in positions:
            if p.model_key != key:
                continue
            day = next((d for d in p.days if d.date == last_session), None)
            if day:
                last_results.append({
                    "position_id": p.id, "ticker": p.ticker, "bucket": p.bucket, "entry_price": p.entry_price,
                    "close": day.close, "high": day.high, "low": day.low, "session_move": round(day.mark / day.prev_mark - 1, 4),
                    "total_return": round(p.ret() or 0, 4), "event": day.event or "held", "your_thesis": p.thesis})
    my_day = sum(d.pnl for d in days if d.model == key and d.date == last_session) if last_session else 0
    return {
        "you_are": model.display_name,
        "model_key": key,
        "generated_at": now_et().isoformat(),
        "tonight": {**next_night, "upload_path": f"inbox/{key}/{next_night['run_date']}.json"},
        # So a briefing that's a day old still tells a bot whether today is a pick night:
        "upcoming_pick_nights": _pick_nights(now_et().date(), 15),
        "rules": RULES,
        "open_positions": [{
            "position_id": p.id, "bucket": p.bucket, "ticker": p.ticker, "entry_date": _d(p.entry_date),
            "entry_price": p.entry_price, "last_price": p.last_price,
            "return_so_far": round(p.ret(), 4) if p.ret() is not None else None,
            "sessions_held": p.sessions_held, "horizon_days": p.horizon_days,
            "sessions_left": max(0, p.horizon_days - p.sessions_held), "target": p.target, "stop": p.stop,
            "your_thesis": p.thesis,
            "your_last_call": ({"action": last_review[p.id].action, "reason": last_review[p.id].reason}
                               if p.id in last_review else None),
        } for p in mine_open if p.entry_price],
        "compounder_slots_free": max(0, config.BUCKETS["compounder"]["max_open"] - comp_open),
        "last_session": {"date": _d(last_session), "your_pnl": round(my_day, 2), "positions": last_results},
        "scoreboard": [{"model": r["model"], "total_pnl": r["total_pnl"], "win_rate": r["win_rate"],
                        "positions": r["positions"]} for r in boards["all"]["all"]],
        "your_recent_lessons": recent_lessons[:6],
        "your_last_upload": None if last_sub is None else {
            "path": last_sub.path, "status": last_sub.status, "errors": last_sub.errors or [],
            "received_at": last_sub.received_at.isoformat() + "Z"},
        "example_submission": {**EXAMPLE_SUBMISSION, "model": key},
    }


CSV_COLUMNS = ["id", "model", "bucket", "ticker", "status", "entry_date", "first_session", "entry_price",
               "orig_target", "orig_stop", "target", "stop", "horizon_days", "sessions_held", "exit_date",
               "exit_price", "exit_reason", "last_price", "return", "pnl_usd", "spy_return", "d1_pct_to_close",
               "d1_pct_to_high", "boom", "confidence", "thesis", "main_risk", "sources", "flags"]


def export_csv(positions, voided, bench_last) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(CSV_COLUMNS)
    for p in sorted([*positions, *voided], key=lambda p: p.id):
        r, d1 = p.ret(), p.d1()
        b = p.benchmark_ret(bench_last)
        w.writerow([p.id, p.model_key, p.bucket, p.ticker, p.status, p.entry_date, p.first_session, p.entry_price,
                    p.orig_target, p.orig_stop, p.target, p.stop, p.horizon_days, p.sessions_held, p.exit_date or "",
                    p.exit_price or "", p.exit_reason or "", p.last_price or "",
                    "" if r is None else round(r, 6), round(p.pnl(), 2), "" if b is None else round(b, 6),
                    round(d1["pct_to_close"], 6) if d1 else "", round(d1["pct_to_high"], 6) if d1 else "",
                    d1.get("boom", "") if d1 else "", p.confidence, p.thesis, p.main_risk,
                    " ".join(p.sources or []), "; ".join(p.flags or [])])
    return buf.getvalue()


def _write(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, separators=(",", ":"), default=str), encoding="utf-8")
