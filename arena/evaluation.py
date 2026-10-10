"""Forward-only evaluation of the two learning models."""
from __future__ import annotations

import statistics
from collections import defaultdict

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import agents, config
from .db import Position


def _metrics(rows: list[dict]) -> dict:
    if not rows:
        return {"observations": 0, "mae": None, "direction_accuracy": None,
                "correlation": None, "mean_reward": None, "mean_predicted": None}
    predicted = [r["predicted"] for r in rows]
    actual = [r["actual"] for r in rows]
    correlation = None
    if len(rows) >= 3 and statistics.pstdev(predicted) > 0 and statistics.pstdev(actual) > 0:
        correlation = float(np.corrcoef(predicted, actual)[0, 1])
    return {
        "observations": len(rows),
        "mae": statistics.fmean(abs(p - a) for p, a in zip(predicted, actual)),
        "direction_accuracy": statistics.fmean((p >= 0) == (a >= 0) for p, a in zip(predicted, actual)),
        "correlation": correlation,
        "mean_reward": statistics.fmean(actual),
        "mean_predicted": statistics.fmean(predicted),
    }


def _walk_forward(rows, feature_fn, reward_fn, dim, prior, noise, warmup=20) -> dict:
    rows = [p for p in rows if p.exit_date and p.first_session and reward_fn(p) is not None]
    outcomes = sorted(rows, key=lambda p: (p.exit_date, p.id))
    decisions = defaultdict(list)
    for p in rows:
        decisions[p.first_session].append(p)
    brain = agents.Brain(dim=dim)
    brain.A = np.eye(dim) * prior
    brain.noise = noise ** 2
    learned, cursor, forward = set(), 0, []
    for day in sorted(decisions):
        while cursor < len(outcomes) and outcomes[cursor].exit_date < day:
            p = outcomes[cursor]
            x, y = feature_fn(p), reward_fn(p)
            if x is not None and y is not None and p.id not in learned:
                brain.learn(np.asarray(x, dtype=float), y)
                learned.add(p.id)
            cursor += 1
        for p in decisions[day]:
            x, y = feature_fn(p), reward_fn(p)
            if x is None or y is None or brain.n < warmup:
                continue
            forward.append({"position_id": p.id, "decision_date": day.isoformat(),
                            "training_observations": brain.n, "predicted": brain.predict(np.asarray(x)),
                            "actual": y})

    full = agents.Brain(dim=dim)
    full.A = np.eye(dim) * prior
    full.noise = noise ** 2
    for p in outcomes:
        x, y = feature_fn(p), reward_fn(p)
        if x is not None and y is not None:
            full.learn(np.asarray(x), y)
    in_sample = []
    for p in rows:
        x, y = feature_fn(p), reward_fn(p)
        if x is not None and y is not None:
            in_sample.append({"predicted": full.predict(np.asarray(x)), "actual": y})
    return {"warmup_observations": warmup, "out_of_sample": _metrics(forward),
            "in_sample": _metrics(in_sample), "recent_forward_predictions": forward[-20:][::-1]}


def evaluate(db: Session) -> dict:
    ai = db.scalars(select(Position).where(Position.status == "closed",
                                           Position.model_key.in_(config.AI_MODELS),
                                           Position.entry_price.isnot(None))).all()
    evo = db.scalars(select(Position).where(Position.status == "closed", Position.model_key == "fly_evo",
                                            Position.selection_features.isnot(None))).all()
    learner_result = _walk_forward(
        ai, agents.features, agents.reward, len(agents.FEATURES), config.LEARNER_PRIOR_PRECISION,
        config.LEARNER_NOISE_SD)
    evo_result = _walk_forward(
        evo, lambda p: p.selection_features, agents._evo_reward, len(agents.EVO_FEATURES),
        config.EVO_PRIOR_PRECISION, config.EVO_NOISE_SD)
    return {
        "method": "expanding-window; each prediction uses only outcomes with exit_date before decision_date",
        "learner": learner_result,
        "fly_evo": evo_result,
        "warning": "In-sample fit is optimistic. Only out-of-sample metrics may be used to discuss generalization.",
    }
