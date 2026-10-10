"""Two contestants that live inside the GitHub Action instead of uploading files.

THE LEARNER: a reinforcement learning agent (a Thompson-sampling contextual bandit).
  * Every pick an AI makes is described by a few features: which AI made it, which book it's in,
    the AI's stated confidence, how far the target and stop are, and how long it may be held.
  * When any AI pick closes, the Learner sees the reward: that trade's return minus the S&P 500's
    return over the same days (so it can't just learn "the market went up").
  * It keeps a Bayesian estimate of how much each feature adds to that reward. The gap between what
    it expected and what happened is its reward-prediction error: the same signal dopamine neurons
    carry in real brains. Positive surprises strengthen the features involved; negative ones weaken them.
  * Each night it scores the AIs' new picks with weights *sampled* from its beliefs (exploration when
    unsure, exploitation once confident) and copies the ones it expects to beat the S&P 500, up to 5.
    Its copies follow the original AI's later hold/sell calls, and are scored like everyone else's.

THE FRUIT FLY: the control group. Random liquid stocks, same three books, fixed exit rules. If an AI
can't beat the fly, its "research" isn't adding anything.

Everything is recomputed from the database on every run, so results are reproducible and auditable.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import random
import statistics
from typing import Optional
from zoneinfo import ZoneInfo

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import config
from .db import Position, Submission
from .engine import ACTIVE, _supersede, fill_entries, now_et
from .market_calendar import is_trading_day, session_plan, should_run_picks_tonight
from .prices import PriceProvider

ET = ZoneInfo("America/New_York")
OPENS = dt.time(9, 20)  # agents stop changing picks shortly before the open
CLOSE_SETTLED = dt.time(16, 10)

FEATURES = [
    "Picked by Claude", "Picked by ChatGPT", "Picked by Grok",
    "Moonshot", "Catalyst play", "Compounder",
    "AI said high confidence", "AI said low confidence",
    "Big upside to target", "Wide stop", "Reward-to-risk ratio", "Longer holding period",
]

EVO_FEATURES = [
    "Intercept", "5-session momentum", "20-session momentum", "20-session strength vs SPY",
    "20-session volatility", "Volume trend", "20-session drawdown",
]


# =========================================================================== shared


def pick_window(now: dt.datetime) -> Optional[tuple[dt.date, dt.date, dt.date]]:
    """(run_date, ref_date, target_date) if agents may pick right now, else None.

    Open from the reference close until just before the next session's open."""
    n = now.astimezone(ET)
    d = n.date()
    if should_run_picks_tonight(d) and n.time() >= CLOSE_SETTLED:
        run = d
    elif is_trading_day(d) and n.time() < OPENS:
        run = d - dt.timedelta(days=1)
        for _ in range(7):
            if should_run_picks_tonight(run) and session_plan(run)[1] == d:
                break
            run -= dt.timedelta(days=1)
        else:
            return None
    else:
        return None
    ref, target = session_plan(run)
    return run, ref, target


def _active_sub(db: Session, model: str, target: dt.date) -> Optional[Submission]:
    return db.scalar(select(Submission).where(Submission.model_key == model, Submission.target_date == target,
                                              Submission.status.in_(ACTIVE)).order_by(Submission.id.desc()))


def _new_sub(db: Session, model: str, run: dt.date, ref: dt.date, target: dt.date, raw: dict, now) -> Submission:
    text = json.dumps(raw, indent=1, default=str)
    sub = Submission(model_key=model, path=f"internal/{model}/{run}", sha=hashlib.sha256(text.encode()).hexdigest(),
                     run_date=run, ref_date=ref, target_date=target, status="ok", errors=[],
                     received_at=now.astimezone(dt.timezone.utc).replace(tzinfo=None), author="arena action",
                     raw=text, market_view=raw.get("market_view", ""), model_version=raw.get("version", ""))
    db.add(sub)
    return sub


# =========================================================================== the Learner


def features(p: Position) -> np.ndarray:
    e = p.entry_price or p.ref_price or 1.0
    up = min(max(p.orig_target / e - 1, 0.0), 1.0)
    down = min(max(1 - p.orig_stop / e, 0.001), 1.0)
    return np.array([
        p.model_key == "claude", p.model_key == "chatgpt", p.model_key == "grok",
        p.bucket == "moonshot", p.bucket == "catalyst", p.bucket == "compounder",
        p.confidence == "high", p.confidence == "low",
        up * 5, down * 10, max(-2.0, min(2.0, math.log(max(up, 0.001) / down))) / 2,
        math.log1p(p.horizon_days) / math.log(121),
    ], dtype=float)


def reward(p: Position) -> Optional[float]:
    """Return vs the S&P 500 over the same days, clipped so one wild trade can't dominate."""
    r = p.ret()
    if r is None:
        return None
    b = p.benchmark_ret()
    return float(max(-0.5, min(0.5, r - (b or 0.0))))


class Brain:
    """Bayesian linear regression updated one trade at a time (so every update has a prediction error)."""

    def __init__(self, dim: int = len(FEATURES)):
        self.A = np.eye(dim) * config.LEARNER_PRIOR_PRECISION
        self.b = np.zeros(dim)
        self.noise = config.LEARNER_NOISE_SD ** 2
        self.n = 0

    @property
    def mean(self) -> np.ndarray:
        return np.linalg.solve(self.A, self.b)

    @property
    def cov(self) -> np.ndarray:
        return np.linalg.inv(self.A)

    def predict(self, x: np.ndarray) -> float:
        return float(x @ self.mean)

    def learn(self, x: np.ndarray, y: float) -> float:
        """Update on one outcome; returns the reward-prediction error (the 'dopamine' signal)."""
        rpe = y - self.predict(x)
        self.A += np.outer(x, x) / self.noise
        self.b += x * y / self.noise
        self.n += 1
        return rpe

    def sample(self, rng: np.random.Generator) -> np.ndarray:
        return rng.multivariate_normal(self.mean, self.cov)


def training_set(db: Session, before: Optional[dt.date] = None) -> list[Position]:
    """Every closed AI pick, in the order the outcomes became known."""
    q = select(Position).where(Position.status == "closed", Position.model_key.in_(config.AI_MODELS),
                               Position.entry_price.isnot(None))
    if before is not None:
        q = q.where(Position.exit_date < before)
    return sorted(db.scalars(q).all(), key=lambda p: (p.exit_date, p.id))


def train(db: Session, before: Optional[dt.date] = None) -> tuple[Brain, list[dict]]:
    brain, events = Brain(), []
    for p in training_set(db, before):
        y = reward(p)
        if y is None:
            continue
        x = features(p)
        expected = brain.predict(x)
        rpe = brain.learn(x, y)
        events.append({"position_id": p.id, "date": p.exit_date.isoformat(), "model": p.model_key, "ticker": p.ticker,
                       "bucket": p.bucket, "reward": y, "expected": expected, "rpe": rpe})
    return brain, events


def run_learner(db: Session, now: Optional[dt.datetime] = None) -> dict:
    now = (now or now_et()).astimezone(ET)
    window = pick_window(now)
    if window is None:
        return {"learner": "outside pick window"}
    run, ref, target = window
    candidates = [p for p in db.scalars(select(Position).join(Submission).where(
        Position.model_key.in_(config.AI_MODELS), Position.first_session == target, Position.status == "open",
        Position.ref_price.isnot(None), Position.sessions_held == 0, Submission.status.in_(ACTIVE))).all()]
    if not candidates:
        return {"learner": "no AI picks yet"}
    brain, _ = train(db, before=target)  # only outcomes known before this session
    rng = np.random.default_rng(int(target.strftime("%Y%m%d")) * 1000 + brain.n)
    w = brain.sample(rng)
    scored = []
    for p in candidates:
        x = features(p)
        scored.append({"position": p, "sampled": float(x @ w), "expected": brain.predict(x),
                       "uncertainty": float(math.sqrt(max(x @ brain.cov @ x, 0)))})
    best: dict[str, dict] = {}
    for s in sorted(scored, key=lambda s: s["sampled"], reverse=True):
        best.setdefault(s["position"].ticker, s)  # one copy per ticker
    chosen = [s for s in best.values() if s["sampled"] > 0][: config.LEARNER_PICKS_PER_NIGHT]

    decision = {
        "version": f"thompson-bandit/{brain.n}-trades",
        "market_view": (f"Learned from {brain.n} closed AI trades. Scored {len(candidates)} picks for {target}; "
                        f"copying {len(chosen)} it expects to beat the S&P 500."),
        "observations": brain.n,
        "chosen": [{"source_position_id": s["position"].id, "ticker": s["position"].ticker,
                    "from": s["position"].model_key, "bucket": s["position"].bucket,
                    "sampled_edge": round(s["sampled"], 5), "expected_edge": round(s["expected"], 5),
                    "uncertainty": round(s["uncertainty"], 5)} for s in chosen],
        "candidates": len(candidates),
    }
    old = _active_sub(db, "learner", target)
    if old is not None:
        old_ids = sorted(p.source_position_id for p in old.positions)
        if old_ids == sorted(c["source_position_id"] for c in decision["chosen"]):
            return {"learner": "unchanged", "chosen": len(chosen)}
        if any(p.days for p in old.positions):
            return {"learner": "session already started"}
        _supersede(db, old)
    sub = _new_sub(db, "learner", run, ref, target, decision, now)
    for rank, s in enumerate(chosen, 1):
        src: Position = s["position"]
        sub.positions.append(Position(
            model_key="learner", bucket=src.bucket, rank=rank, ticker=src.ticker,
            thesis=f"Copied from {config.MODELS[src.model_key]['display_name']}: {src.thesis}"[:600],
            catalyst_time=src.catalyst_time, sources=src.sources, entry_zone_low=src.entry_zone_low,
            entry_zone_high=src.entry_zone_high, confidence=src.confidence,
            main_risk=f"Expected edge vs S&P 500: {s['expected']:+.2%} (±{s['uncertainty']:.2%}). {src.main_risk}"[:600],
            horizon_days=src.horizon_days, orig_target=src.orig_target, orig_stop=src.orig_stop,
            target=src.target, stop=src.stop, entry_date=src.entry_date, first_session=src.first_session,
            ref_price=src.ref_price,
            source_position_id=src.id))
    db.commit()
    return {"learner": "picked", "chosen": len(chosen), "observations": brain.n}


def learner_state(db: Session) -> dict:
    """What the Learner currently believes, for the site."""
    brain, events = train(db)
    mean, sd = brain.mean, np.sqrt(np.diag(brain.cov))
    weights = [{"feature": f, "mean": float(m), "sd": float(s)} for f, m, s in zip(FEATURES, mean, sd)]
    weights.sort(key=lambda w: abs(w["mean"]), reverse=True)
    history, n = [], 0
    by_day: dict[str, list[float]] = {}
    for e in events:
        by_day.setdefault(e["date"], []).append(e["rpe"])
    for day in sorted(by_day):
        n += len(by_day[day])
        history.append({"date": day, "observations": n, "avg_abs_surprise": float(np.mean(np.abs(by_day[day])))})
    return {"observations": brain.n, "weights": weights, "recent": events[-20:][::-1], "history": history,
            "features": FEATURES}


# =========================================================================== Fruit Fly EVO


def _evo_reward(p: Position) -> Optional[float]:
    """Risk-adjusted excess return using only the realized path of a completed trade."""
    if p.status != "closed" or not p.entry_price or p.exit_price is None:
        return None
    peak = p.entry_price
    max_drawdown = 0.0
    for day in sorted(p.days, key=lambda d: d.date):
        peak = max(peak, day.high)
        max_drawdown = min(max_drawdown, day.low / peak - 1)
    benchmark = p.benchmark_ret()
    if benchmark is None:
        return None
    raw = (p.gross_ret() or 0.0) - benchmark - config.EVO_DRAWDOWN_PENALTY * abs(max_drawdown) \
          - 2 * config.COST_PER_SIDE
    return float(max(-config.EVO_REWARD_CLIP, min(config.EVO_REWARD_CLIP, raw)))


def _train_evo(db: Session, before: Optional[dt.date] = None) -> tuple[Brain, list[dict]]:
    brain = Brain(dim=len(EVO_FEATURES))
    brain.A = np.eye(len(EVO_FEATURES)) * config.EVO_PRIOR_PRECISION
    brain.noise = config.EVO_NOISE_SD ** 2
    q = select(Position).where(Position.model_key == "fly_evo", Position.status == "closed",
                               Position.selection_features.isnot(None))
    if before is not None:
        q = q.where(Position.exit_date < before)
    rows = sorted(db.scalars(q).all(), key=lambda p: (p.exit_date, p.id))
    events = []
    for p in rows:
        y = _evo_reward(p)
        if y is None:
            continue
        x = np.asarray(p.selection_features, dtype=float)
        if x.shape != (len(EVO_FEATURES),) or not np.all(np.isfinite(x)):
            continue
        expected = brain.predict(x)
        rpe = brain.learn(x, y)
        events.append({"position_id": p.id, "date": p.exit_date.isoformat(), "ticker": p.ticker,
                       "bucket": p.bucket, "reward": y, "expected": expected, "rpe": rpe})
    return brain, events


def _signal_vector(bars: dict[dt.date, object], spy: dict[dt.date, object], ref: dt.date) -> Optional[list[float]]:
    rows = [b for d, b in sorted(bars.items()) if d <= ref][-21:]
    spy_rows = [b for d, b in sorted(spy.items()) if d <= ref][-21:]
    if len(rows) < 21 or len(spy_rows) < 21 or rows[-1].close <= config.MIN_PRICE:
        return None
    closes = [b.close for b in rows]
    returns = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
    spy_ret = spy_rows[-1].close / spy_rows[0].close - 1
    vols = [b.volume for b in rows]
    avg_volume = statistics.fmean(vols[-20:])
    if avg_volume < config.MIN_AVG_VOLUME:
        return None
    peak = max(closes)
    vector = [
        1.0,
        max(-1.0, min(1.0, (closes[-1] / closes[-6] - 1) * 5)),
        max(-1.0, min(1.0, (closes[-1] / closes[0] - 1) * 3)),
        max(-1.0, min(1.0, ((closes[-1] / closes[0] - 1) - spy_ret) * 3)),
        max(0.0, min(1.0, statistics.pstdev(returns) * math.sqrt(252) / 1.5)),
        max(-1.0, min(1.0, (statistics.fmean(vols[-5:]) / avg_volume - 1))),
        max(-1.0, min(0.0, (closes[-1] / peak - 1) * 3)),
    ]
    return vector


def run_evo(db: Session, provider: PriceProvider, now: Optional[dt.datetime] = None) -> dict:
    """Select independent stocks with a reproducible Bayesian contextual bandit."""
    now = (now or now_et()).astimezone(ET)
    window = pick_window(now)
    if window is None:
        return {"fly_evo": "outside pick window"}
    run, ref, target = window
    if _active_sub(db, "fly_evo", target) is not None:
        return {"fly_evo": "already picked"}

    held_rows = db.scalars(select(Position).where(Position.model_key == "fly_evo",
                                                  Position.status == "open")).all()
    held = {p.ticker for p in held_rows}
    comp_open = sum(p.bucket == "compounder" for p in held_rows)
    pool = [t for t in FLY_UNIVERSE if t not in held]
    rng = random.Random(f"fruit-fly-evo-universe-{run}")
    rng.shuffle(pool)
    history: dict[str, dict] = {}
    spy = {}
    failed_batches = 0
    for i in range(0, len(pool), 10):
        batch = pool[i:i + 10]
        try:
            found = provider.history([*batch, config.BENCHMARK], ref, calendar_days=50)
        except Exception:
            failed_batches += 1
            if failed_batches >= 3:
                break
            continue
        spy.update(found.get(config.BENCHMARK, {}))
        for ticker in batch:
            if found.get(ticker):
                history[ticker] = found[ticker]

    brain, _ = _train_evo(db, before=target)
    sample_rng = np.random.default_rng(int(target.strftime("%Y%m%d")) * 10_000 + brain.n)
    weights = brain.sample(sample_rng)
    candidates = []
    for ticker, bars in history.items():
        x = _signal_vector(bars, spy, ref)
        if x is None:
            continue
        close = bars[ref].close if ref in bars else None
        if close is None:
            continue
        arr = np.asarray(x)
        candidates.append({"ticker": ticker, "close": close, "features": x,
                           "sampled": float(arr @ weights), "expected": brain.predict(arr),
                           "uncertainty": float(math.sqrt(max(arr @ brain.cov @ arr, 0)))})
    candidates.sort(key=lambda row: (row["sampled"], row["ticker"]), reverse=True)

    needed = 10 + max(0, config.BUCKETS["compounder"]["max_open"] - comp_open)
    if len(candidates) < needed:
        return {"fly_evo": "insufficient eligible history; retry on next run", "eligible": len(candidates),
                "needed": needed, "reference_date": ref.isoformat(), "failed_batches": failed_batches}

    plan, cursor = [], 0
    for bucket, rule in config.FLY_RULES.items():
        n = rule["n"] if rule["n"] is not None else max(0, config.BUCKETS["compounder"]["max_open"] - comp_open)
        for _ in range(n):
            plan.append((bucket, candidates[cursor], rule))
            cursor += 1
    raw = {
        "version": config.EVO_MODEL_VERSION,
        "data_version": config.EVO_DATA_VERSION,
        "market_view": (f"Independent contextual bandit trained on {brain.n} completed EVO trades. "
                        f"Ranked {len(candidates)} liquid stocks using only data through {ref}."),
        "observations": brain.n,
        "exploration_seed": int(target.strftime("%Y%m%d")) * 10_000 + brain.n,
        "picks": [{"bucket": b, "ticker": row["ticker"], "sampled_score": round(row["sampled"], 6),
                   "expected_reward": round(row["expected"], 6),
                   "uncertainty": round(row["uncertainty"], 6)} for b, row, _ in plan],
    }
    sub = _new_sub(db, "fly_evo", run, ref, target, raw, now)
    for rank, (bucket, row, rule) in enumerate(plan, 1):
        c = row["close"]
        labels = sorted(zip(EVO_FEATURES, row["features"]), key=lambda item: abs(item[1]), reverse=True)
        explanation = ", ".join(f"{label} {value:+.2f}" for label, value in labels[1:4])
        sub.positions.append(Position(
            model_key="fly_evo", bucket=bucket, rank=rank, ticker=row["ticker"],
            thesis=f"Bandit selection from measured signals: {explanation}.", confidence="medium",
            main_risk=(f"Estimated reward {row['expected']:+.2%}; posterior uncertainty "
                       f"{row['uncertainty']:.2%}. Signals may not persist."),
            horizon_days=rule["horizon"], orig_target=round(c * (1 + rule["target"]), 2),
            orig_stop=round(c * (1 - rule["stop"]), 2), target=round(c * (1 + rule["target"]), 2),
            stop=round(c * (1 - rule["stop"]), 2), entry_date=ref, first_session=target,
            ref_price=round(c, 4), selection_features=row["features"], agent_version=config.EVO_MODEL_VERSION))
    db.commit()
    return {"fly_evo": "picked", "picks": len(plan), "observations": brain.n,
            "eligible": len(candidates), "failed_batches": failed_batches}


def evo_state(db: Session) -> dict:
    brain, events = _train_evo(db)
    mean, sd = brain.mean, np.sqrt(np.diag(brain.cov))
    weights = [{"feature": f, "mean": float(m), "sd": float(s)} for f, m, s in zip(EVO_FEATURES, mean, sd)]
    weights.sort(key=lambda w: abs(w["mean"]), reverse=True)
    cumulative, history = 0.0, []
    for event in events:
        cumulative += event["reward"]
        history.append({**event, "cumulative_reward": cumulative})
    return {"version": config.EVO_MODEL_VERSION, "data_version": config.EVO_DATA_VERSION,
            "observations": brain.n, "cumulative_reward": cumulative, "weights": weights,
            "recent": events[-20:][::-1], "history": history,
            "reward": "gross return - SPY return - drawdown penalty - round-trip trading costs"}


# =========================================================================== the Fruit Fly

FLY_UNIVERSE = [
    # Liquid, well-known NYSE/Nasdaq names across sectors. Any that fail the listing rules are voided.
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "AMD", "ORCL", "CRM", "ADBE", "INTC", "QCOM",
    "TXN", "MU", "AMAT", "LRCX", "KLAC", "ADI", "MRVL", "NOW", "INTU", "PANW", "CRWD", "SNOW", "NET", "DDOG", "ZS",
    "SHOP", "UBER", "ABNB", "DASH", "PLTR", "COIN", "HOOD", "SOFI", "PYPL", "SQ", "AFRM", "V", "MA", "AXP", "JPM",
    "BAC", "WFC", "C", "GS", "MS", "SCHW", "BLK", "BRK.B", "UNH", "LLY", "JNJ", "PFE", "MRK", "ABBV", "BMY", "AMGN",
    "GILD", "MRNA", "VRTX", "REGN", "ISRG", "TMO", "DHR", "ABT", "CVS", "HUM", "XOM", "CVX", "COP", "OXY", "SLB",
    "HAL", "DVN", "CAT", "DE", "BA", "GE", "HON", "LMT", "RTX", "UPS", "FDX", "DAL", "UAL", "AAL", "CCL", "RCL",
    "NKE", "LULU", "SBUX", "MCD", "CMG", "KO", "PEP", "PG", "COST", "WMT", "TGT", "HD", "LOW", "DIS", "NFLX", "ROKU",
    "SPOT", "T", "VZ", "TMUS", "NEE", "DUK", "SO", "F", "GM", "RIVN", "LCID", "NIO", "ENPH", "FSLR", "VST", "CEG",
    "SMCI", "ARM", "DELL", "HPQ", "IBM", "CSCO", "PINS", "SNAP", "RBLX", "U", "DKNG", "MSTR", "RKLB", "IONQ", "HIMS",
]


def run_momentum(db: Session, provider: PriceProvider, now: Optional[dt.datetime] = None) -> dict:
    """Point-in-time 20-session momentum baseline with no learned parameters."""
    now = (now or now_et()).astimezone(ET)
    window = pick_window(now)
    if window is None:
        return {"momentum": "outside pick window"}
    run, ref, target = window
    if _active_sub(db, "momentum", target) is not None:
        return {"momentum": "already picked"}
    held_rows = db.scalars(select(Position).where(Position.model_key == "momentum",
                                                  Position.status == "open")).all()
    held = {p.ticker for p in held_rows}
    comp_open = sum(p.bucket == "compounder" for p in held_rows)
    pool = [t for t in FLY_UNIVERSE if t not in held]
    history, spy, failed_batches = {}, {}, 0
    for i in range(0, len(pool), 10):
        batch = pool[i:i + 10]
        try:
            found = provider.history([*batch, config.BENCHMARK], ref, calendar_days=50)
        except Exception:
            failed_batches += 1
            if failed_batches >= 3:
                break
            continue
        spy.update(found.get(config.BENCHMARK, {}))
        for ticker in batch:
            if found.get(ticker):
                history[ticker] = found[ticker]
    candidates = []
    for ticker, bars in history.items():
        x = _signal_vector(bars, spy, ref)
        if x is None or ref not in bars:
            continue
        candidates.append({"ticker": ticker, "close": bars[ref].close, "features": x, "score": x[2]})
    candidates.sort(key=lambda row: (row["score"], row["ticker"]), reverse=True)
    needed = 10 + max(0, config.BUCKETS["compounder"]["max_open"] - comp_open)
    if len(candidates) < needed:
        return {"momentum": "insufficient eligible history; retry on next run", "eligible": len(candidates),
                "needed": needed, "reference_date": ref.isoformat(), "failed_batches": failed_batches}
    plan, cursor = [], 0
    for bucket, rule in config.FLY_RULES.items():
        n = rule["n"] if rule["n"] is not None else max(0, config.BUCKETS["compounder"]["max_open"] - comp_open)
        for _ in range(n):
            plan.append((bucket, candidates[cursor], rule))
            cursor += 1
    raw = {"version": "simple-momentum/1", "data_version": config.EVO_DATA_VERSION,
           "market_view": f"Rules baseline ranked {len(candidates)} stocks by trailing 20-session momentum through {ref}.",
           "picks": [{"bucket": b, "ticker": row["ticker"], "momentum_score": round(row["score"], 6)}
                     for b, row, _ in plan]}
    sub = _new_sub(db, "momentum", run, ref, target, raw, now)
    for rank, (bucket, row, rule) in enumerate(plan, 1):
        c = row["close"]
        sub.positions.append(Position(
            model_key="momentum", bucket=bucket, rank=rank, ticker=row["ticker"],
            thesis=f"Rules baseline: trailing 20-session momentum score {row['score']:+.3f}.",
            confidence="medium", main_risk="Recent momentum can reverse and is not a forecast.",
            horizon_days=rule["horizon"], orig_target=round(c * (1 + rule["target"]), 2),
            orig_stop=round(c * (1 - rule["stop"]), 2), target=round(c * (1 + rule["target"]), 2),
            stop=round(c * (1 - rule["stop"]), 2), entry_date=ref, first_session=target,
            ref_price=round(c, 4), selection_features=row["features"], agent_version="simple-momentum/1"))
    db.commit()
    return {"momentum": "picked", "picks": len(plan), "eligible": len(candidates),
            "failed_batches": failed_batches}


def run_fly(db: Session, provider: PriceProvider, now: Optional[dt.datetime] = None) -> dict:
    now = (now or now_et()).astimezone(ET)
    window = pick_window(now)
    if window is None:
        return {"fly": "outside pick window"}
    run, ref, target = window
    if _active_sub(db, "fly", target) is not None:
        return {"fly": "already picked"}
    rng = random.Random(f"fruit-fly-{run}")
    held = {p.ticker for p in db.scalars(select(Position).where(Position.model_key == "fly",
                                                                Position.status == "open")).all()}
    comp_open = sum(1 for p in db.scalars(select(Position).where(Position.model_key == "fly", Position.status == "open",
                                                                 Position.bucket == "compounder")).all())
    pool = [t for t in FLY_UNIVERSE if t not in held]
    rng.shuffle(pool)
    # Fetch in small batches. Yahoo sometimes fails large multi-symbol requests;
    # a failed batch must not prevent the control from making any picks.
    # Do not scan future data: only the last completed session is eligible.
    needed = sum(rule["n"] or 0 for rule in config.FLY_RULES.values())
    needed += max(0, config.BUCKETS["compounder"]["max_open"] - comp_open)
    bars = {}
    usable = []
    failed_batches = 0
    for i in range(0, len(pool), 10):
        batch = pool[i:i + 10]
        try:
            found = provider.bars_on(batch, ref)
        except Exception:
            failed_batches += 1
            if failed_batches >= 3:
                break
            continue
        for ticker in batch:
            bar = found.get(ticker)
            if (bar is not None and math.isfinite(bar.close)
                    and bar.close > config.MIN_PRICE
                    and bar.volume >= config.MIN_AVG_VOLUME):
                usable.append(ticker)
                bars[ticker] = bar
        if len(usable) >= needed:
            break
    if not usable:
        return {"fly": "no eligible reference prices; retry on next run",
                "reference_date": ref.isoformat(), "failed_batches": failed_batches}
    plan = []
    for bucket, rule in config.FLY_RULES.items():
        n = rule["n"] if rule["n"] is not None else max(0, config.BUCKETS["compounder"]["max_open"] - comp_open)
        for _ in range(n):
            if not usable:
                break
            plan.append((bucket, usable.pop(0), rule))
    raw = {"version": "uniform-random", "market_view": "Picked at random. If an AI can't beat this, its research isn't adding anything.",
           "picks": [{"bucket": b, "ticker": t} for b, t, _ in plan]}
    sub = _new_sub(db, "fly", run, ref, target, raw, now)
    for rank, (bucket, t, rule) in enumerate(plan, 1):
        c = bars[t].close
        sub.positions.append(Position(
            model_key="fly", bucket=bucket, rank=rank, ticker=t, thesis="Random pick (control group).",
            confidence="low", main_risk="It's random.", horizon_days=rule["horizon"],
            orig_target=round(c * (1 + rule["target"]), 2), orig_stop=round(c * (1 - rule["stop"]), 2),
            target=round(c * (1 + rule["target"]), 2), stop=round(c * (1 - rule["stop"]), 2),
            entry_date=ref, first_session=target))
    db.flush()
    fill_entries(db, provider, list(sub.positions), now)
    db.commit()
    return {"fly": "picked", "picks": len(plan)}
