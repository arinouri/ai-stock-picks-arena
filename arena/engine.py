"""Ingest bot submissions and run the daily position engine."""
from __future__ import annotations

import datetime as dt
import hashlib
import logging
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import config
from .db import Benchmark, Position, PositionDay, Review, Submission
from .market_calendar import (
    is_trading_day,
    last_trading_day_on_or_before,
    next_trading_day,
    previous_trading_day,
    session_plan,
    should_run_picks_tonight,
)
from .prices import Bar, PriceProvider
from .schema import parse_submission

log = logging.getLogger(__name__)
ET = ZoneInfo("America/New_York")
CLOSE_SETTLED = dt.time(16, 10)
ACTIVE = ("ok", "partial")


def now_et() -> dt.datetime:
    return dt.datetime.now(ET)


def sha256(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def last_closed_session(now: dt.datetime) -> dt.date:
    n = now.astimezone(ET)
    if is_trading_day(n.date()) and n.time() >= CLOSE_SETTLED:
        return n.date()
    return previous_trading_day(n.date()) if is_trading_day(n.date()) else last_trading_day_on_or_before(n.date())


def close_is_final(day: dt.date, now: dt.datetime) -> bool:
    return last_closed_session(now) >= day


# =========================================================================== ingest


def ingest_file(db: Session, provider: PriceProvider, path: Path, inbox_root: Path, now: dt.datetime,
                author: str = "") -> Optional[Submission]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    rel = path.relative_to(inbox_root)
    model_key = rel.parts[0] if len(rel.parts) > 1 else ""
    return ingest(db, provider, model_key, str(Path("inbox") / rel), path.stem, raw, now, author)


def ingest(db: Session, provider: PriceProvider, model_key: str, path: str, stem: str, raw: str,
           now: dt.datetime, author: str = "") -> Optional[Submission]:
    """Store one submission and open its positions. Returns None if this exact file was already ingested."""
    now = now.astimezone(ET)
    digest = sha256(raw)
    if db.scalar(select(Submission).where(Submission.sha == digest, Submission.path == path)):
        return None

    errors: list[str] = []
    try:
        run_date = dt.date.fromisoformat(stem[:10])
    except ValueError:
        run_date = now.date()
        errors.append(f"file name must be the date you made the picks, like {now.date()}.json")
    ref_date, target_date = session_plan(run_date)
    sub = Submission(model_key=model_key, path=path, sha=digest, run_date=run_date, ref_date=ref_date,
                     target_date=target_date, received_at=now.astimezone(dt.timezone.utc).replace(tzinfo=None),
                     author=author[:128], raw=raw[:200_000])

    if model_key not in config.AI_MODELS:
        log.warning("ignoring %s: unknown model folder %r", path, model_key)
        return None
    parsed = parse_submission(raw)
    sub.market_view, sub.lessons, sub.model_version = parsed.market_view, parsed.lessons, parsed.model_version
    errors += parsed.errors

    deadline = dt.datetime.combine(run_date, config.SUBMISSION_DEADLINE, ET)
    if errors and not parsed.picks and not parsed.reviews:
        sub.status = "rejected"
    elif not should_run_picks_tonight(run_date):
        sub.status = "rejected"
        errors.append(f"{run_date} is not the evening before a trading session; the next one is "
                      f"{_next_pick_night(now.date())}")
    elif run_date > now.date():
        sub.status = "rejected"
        errors.append("file is dated in the future")
    elif now > deadline:
        sub.status = "late"
        errors.append(f"arrived {now:%Y-%m-%d %H:%M} ET, after the {deadline:%H:%M} ET deadline; not counted")
    db.add(sub)
    if sub.status in ("rejected", "late"):
        sub.errors = errors
        db.flush()
        return sub

    # A newer file for the same night replaces the old one (only possible before the deadline)
    for old in db.scalars(select(Submission).where(Submission.model_key == model_key,
                                                   Submission.target_date == target_date,
                                                   Submission.status.in_(ACTIVE))).all():
        _supersede(db, old)

    open_positions = {p.id: p for p in db.scalars(select(Position).where(
        Position.model_key == model_key, Position.status == "open",
        Position.first_session <= target_date)).all()}

    # ---- reviews (HOLD/SELL on open positions)
    selling: set[int] = set()
    for r in parsed.reviews:
        pos = open_positions.get(r.position_id)
        if pos is None:
            errors.append(f"review: position {r.position_id} is not one of your open positions")
            continue
        new_target = r.new_target if r.new_target and r.new_target > (r.new_stop or pos.stop) else None
        new_stop = r.new_stop if r.new_stop and r.new_stop < (r.new_target or pos.target) else None
        if (r.new_target and new_target is None) or (r.new_stop and new_stop is None):
            errors.append(f"review {pos.ticker}: new_stop must stay below new_target; ignored")
        sub.reviews.append(Review(position_id=pos.id, action=r.action, reason=r.reason, new_stop=new_stop,
                                  new_target=new_target, effective_date=target_date))
        if r.action == "SELL":
            selling.add(pos.id)
            pos.sell_at_open_on = target_date

    # ---- new picks, per bucket
    by_bucket: dict[str, list] = {b: [] for b in config.BUCKETS}
    for p in parsed.picks:
        by_bucket[p.bucket].append(p)
    accepted = []
    for bucket, rule in config.BUCKETS.items():
        picks = by_bucket[bucket]
        if rule["max_open"] is not None:
            held = sum(1 for p in open_positions.values() if p.bucket == bucket and p.id not in selling)
            room = max(0, rule["max_open"] - held)
            if len(picks) > room:
                errors.append(f"{bucket}: book holds max {rule['max_open']}; you have {held} after sells, "
                              f"so only {room} new accepted")
            picks = picks[:room]
        else:
            want = rule["new_per_night"]
            if len(picks) > want:
                errors.append(f"{bucket}: only the first {want} picks count")
                picks = picks[:want]
            elif len(picks) < want:
                errors.append(f"{bucket}: expected {want} picks, got {len(picks)}")
        accepted += picks

    for rank, p in enumerate(accepted, 1):
        sub.positions.append(Position(
            model_key=model_key, bucket=p.bucket, rank=rank, ticker=p.ticker, thesis=p.thesis,
            catalyst_time=p.catalyst_time, sources=p.sources, entry_zone_low=p.entry_zone_low,
            entry_zone_high=p.entry_zone_high, confidence=p.confidence, main_risk=p.main_risk,
            horizon_days=p.horizon_days, orig_target=p.target_price, orig_stop=p.stop_price,
            target=p.target_price, stop=p.stop_price, entry_date=ref_date, first_session=target_date,
        ))
    db.flush()
    errors += fill_entries(db, provider, list(sub.positions), now)
    sub.errors = errors
    live = [p for p in sub.positions if p.status != "void"]
    sub.status = "ok" if not errors else ("partial" if live or sub.reviews else "rejected")
    db.flush()
    return sub


def _next_pick_night(d: dt.date) -> dt.date:
    while not should_run_picks_tonight(d):
        d += dt.timedelta(days=1)
    return d


def _supersede(db: Session, old: Submission) -> None:
    old.status = "superseded"
    for p in list(old.positions):
        if p.days:  # already trading (shouldn't happen before the deadline)
            continue
        db.delete(p)
    for r in list(old.reviews):
        if r.action == "SELL" and r.position.sell_at_open_on == r.effective_date:
            r.position.sell_at_open_on = None
        db.delete(r)
    db.flush()


def fill_entries(db: Session, provider: PriceProvider, positions: list[Position], now: dt.datetime) -> list[str]:
    """Record the reference close and enforce the listing rules. Invalid picks are voided.

    The position is bought later, at the open of its first session (see score)."""
    todo = [p for p in positions if p.ref_price is None and p.status == "open" and close_is_final(p.entry_date, now)]
    if not todo:
        return []
    errors = []
    by_date: dict[dt.date, list[Position]] = {}
    for p in todo:
        by_date.setdefault(p.entry_date, []).append(p)
    for ref_date, group in by_date.items():
        tickers = sorted({p.ticker for p in group} | {config.BENCHMARK})
        try:
            hist = provider.history(tickers, ref_date, calendar_days=40)
        except Exception as e:  # network trouble: try again next run
            log.warning("price history failed: %s", e)
            continue
        bench = hist.get(config.BENCHMARK, {}).get(ref_date)
        for p in group:
            bars = hist.get(p.ticker, {})
            bar = bars.get(ref_date)
            problem = None
            if bar is None:
                problem = "no price data (not a NYSE/Nasdaq stock, or delisted)"
            elif bar.close <= config.MIN_PRICE:
                problem = f"price ${bar.close:.2f} is not above ${config.MIN_PRICE:.0f}"
            else:
                vols = [b.volume for d, b in sorted(bars.items()) if d <= ref_date][-20:]
                avg = sum(vols) / len(vols) if vols else 0
                if vols and avg < config.MIN_AVG_VOLUME:
                    problem = f"average volume {avg / 1e3:.0f}K is under 500K"
                elif p.target <= bar.close:
                    problem = f"target ${p.target:.2f} is not above the entry price ${bar.close:.2f}"
                elif p.stop >= bar.close:
                    problem = f"stop ${p.stop:.2f} is not below the entry price ${bar.close:.2f}"
            if problem:
                p.status, p.exit_reason = "void", "void"
                p.flags = [problem]
                errors.append(f"{p.bucket} {p.ticker}: {problem}; pick voided")
            else:
                p.ref_price = round(bar.close, 4)  # checked against the rules; the buy happens at the next open
    db.flush()
    return errors


# =========================================================================== daily engine


def step(pos: Position, day: dt.date, bar: Bar, sell_at_open: bool) -> Optional[str]:
    """Advance one session. Returns the exit reason if the position closed.

    Order of checks: model SELL (exit at the open) → stop (if the day touched both stop and target we
    can't know which came first, so the stop wins) → target → time limit (exit at the close).
    Gaps are honest: a gap below the stop exits at the open, not at the stop price.
    """
    prev = pos.last_price if pos.last_price is not None else pos.entry_price
    pos.sessions_held += 1
    reason, price = None, bar.close
    if sell_at_open:
        reason, price = "model_sell", bar.open
    elif bar.low <= pos.stop:
        reason, price = "stop", min(bar.open, pos.stop)
    elif bar.high >= pos.target:
        reason, price = "target", max(bar.open, pos.target)
    elif pos.sessions_held >= pos.horizon_days:
        reason, price = "time", bar.close
    if pos.sessions_held == 1:
        pos.d1_open, pos.d1_high, pos.d1_low, pos.d1_close = bar.open, bar.high, bar.low, bar.close
    pos.days.append(PositionDay(date=day, open=bar.open, high=bar.high, low=bar.low, close=bar.close,
                                mark=round(price, 4), prev_mark=prev, event=reason))
    pos.last_date, pos.last_price, pos.missing_sessions = day, round(price, 4), 0
    if reason:
        pos.status, pos.exit_date, pos.exit_price, pos.exit_reason = "closed", day, round(price, 4), reason
        pos.sell_at_open_on = None
    return reason


def _sessions(start: dt.date, end: dt.date) -> list[dt.date]:
    out, d = [], start
    while d <= end:
        if is_trading_day(d):
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def score(db: Session, provider: PriceProvider, now: Optional[dt.datetime] = None, with_intraday: bool = True) -> dict:
    """Process every session that has closed since each open position was last updated. Idempotent."""
    now = (now or now_et()).astimezone(ET)
    last = last_closed_session(now)
    fill_entries(db, provider, db.scalars(select(Position).where(Position.status == "open",
                                                                 Position.ref_price.is_(None))).all(), now)
    positions = db.scalars(select(Position).where(Position.status == "open", Position.ref_price.isnot(None),
                                                  Position.first_session <= last)).all()
    if not positions:
        _update_benchmark(db, provider, last)
        db.commit()
        return {"processed_sessions": 0, "closed": 0, "last_session": last.isoformat()}

    start = min((p.last_date and next_trading_day(p.last_date)) or p.first_session for p in positions)
    tickers = sorted({p.ticker for p in positions})
    try:
        bars = provider.daily_bars(tickers, start, last)
    except Exception as e:
        log.warning("daily bars failed: %s", e)
        return {"error": str(e)}

    _update_benchmark(db, provider, last, since=min(p.entry_date for p in positions))
    bench_open = {b.date: b.open for b in db.scalars(select(Benchmark)).all() if b.open}
    reviews: dict[tuple[int, dt.date], list[Review]] = {}
    for r in db.scalars(select(Review).join(Submission).where(Submission.status.in_(ACTIVE),
                                                              Review.effective_date >= start)).all():
        reviews.setdefault((r.position_id, r.effective_date), []).append(r)

    processed, closed, first_days = 0, 0, []
    for pos in positions:
        begin = next_trading_day(pos.last_date) if pos.last_date else pos.first_session
        for day in _sessions(begin, last):
            bar = bars.get(pos.ticker, {}).get(day)
            if bar is None:
                pos.missing_sessions += 1
                if pos.missing_sessions >= config.VOID_AFTER_MISSING_SESSIONS:
                    if pos.sessions_held == 0:
                        pos.status, pos.exit_reason = "void", "void"
                        pos.flags = (pos.flags or []) + ["no price data after entry"]
                    else:
                        pos.status, pos.exit_date, pos.exit_price, pos.exit_reason = (
                            "closed", pos.last_date, pos.last_price, "no_data")
                    break
                continue
            sell = False
            # The Learner's positions copy an AI's pick, so they follow that AI's nightly calls too
            for r in reviews.get((pos.id, day), []) + reviews.get((pos.source_position_id, day), []):
                if r.new_stop:
                    pos.stop = r.new_stop
                if r.new_target:
                    pos.target = r.new_target
                sell = sell or r.action == "SELL"
            if pos.sessions_held == 0:
                first_days.append(pos)
                if pos.entry_price is None:  # bought at the open, the first moment anyone could act on the pick
                    pos.entry_price = round(bar.open, 4)
                    pos.last_price = pos.entry_price
                    pos.benchmark_entry = bench_open.get(day)
            processed += 1
            if step(pos, day, bar, sell):
                closed += 1
                break
    _update_benchmark(db, provider, last, since=min(p.entry_date for p in positions))
    bench = {b.date: b.close for b in db.scalars(select(Benchmark)).all()}
    for pos in positions:
        if pos.status == "closed" and pos.benchmark_exit is None:
            pos.benchmark_exit = bench.get(pos.exit_date)
        if pos.benchmark_entry is None:
            pos.benchmark_entry = bench.get(pos.entry_date)
    if with_intraday:
        for pos in first_days:
            if pos.bucket in ("moonshot", "catalyst") and pos.d1_close is not None:
                try:
                    pos.d1_intraday = provider.intraday(pos.ticker, pos.first_session) or None
                except Exception:
                    pass
    db.commit()
    return {"processed_sessions": processed, "closed": closed, "last_session": last.isoformat()}


def _update_benchmark(db: Session, provider: PriceProvider, last: dt.date, since: Optional[dt.date] = None) -> None:
    have = set(db.scalars(select(Benchmark.date).where(Benchmark.open.isnot(None))).all())
    needed = [d for d in _sessions(since or last - dt.timedelta(days=45), last) if d not in have]
    if not needed:
        return
    try:
        bars = provider.daily_bars([config.BENCHMARK], min(needed), last).get(config.BENCHMARK, {})
    except Exception as e:
        log.warning("benchmark fetch failed: %s", e)
        return
    for d, b in bars.items():
        if d in have:
            continue
        row = db.get(Benchmark, d)
        if row is None:
            db.add(Benchmark(date=d, close=b.close, open=b.open))
        else:
            row.open = b.open
    db.flush()
