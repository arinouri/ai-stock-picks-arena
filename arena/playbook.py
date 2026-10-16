"""The shared playbook: what every AI gets to read each night about what the whole arena has learned.

Built only from the database, so it is reproducible. It has four parts:
  * peer lessons   - the lessons the AIs wrote for themselves, readable by the other AIs
  * evidence       - results by AI, book, confidence and stop width (with sample sizes)
  * examples       - recent winners and losers with the thesis that was behind them
  * baselines      - what the random and rules-based contestants did, so skill can be told from luck
Plus the owner's standing instructions from updates/ (see updates/README.md).
"""
from __future__ import annotations

from pathlib import Path
from statistics import mean
from typing import Optional

from . import config

MIN_N = 20  # below this many closed trades, a pattern is noise and is labelled as such


def _closed(positions, models):
    return [p for p in positions if p.status == "closed" and p.model_key in models and p.ret() is not None]


def _summary(ps) -> dict:
    rets = [p.ret() for p in ps]
    alpha = [p.ret() - p.benchmark_ret() for p in ps if p.benchmark_ret() is not None]
    return {
        "n": len(ps),
        "avg_return": round(mean(rets), 4) if rets else None,
        "win_rate": round(sum(r > 0 for r in rets) / len(rets), 3) if rets else None,
        "avg_vs_spy": round(mean(alpha), 4) if alpha else None,
        "stop_rate": round(sum(p.exit_reason == "stop" for p in ps) / len(ps), 3) if ps else None,
        "target_rate": round(sum(p.exit_reason == "target" for p in ps) / len(ps), 3) if ps else None,
        "reliable": len(ps) >= MIN_N,
    }


def _stop_width(p) -> Optional[str]:
    if not p.ref_price or not p.orig_stop:
        return None
    w = 1 - p.orig_stop / p.ref_price
    return "tight stop (under 4%)" if w < 0.04 else "medium stop (4-8%)" if w < 0.08 else "wide stop (8%+)"


def _example(p) -> dict:
    return {"model": p.model_key, "ticker": p.ticker, "book": p.bucket, "return": round(p.ret(), 4),
            "exit": p.exit_reason, "confidence": p.confidence, "thesis": (p.thesis or "")[:240],
            "main_risk": (p.main_risk or "")[:160], "date": p.exit_date.isoformat() if p.exit_date else None}


def read_updates(root: Path, key: Optional[str] = None) -> list[dict]:
    """Standing instructions from the owner: updates/*.md (for everyone) and updates/<key>.md (for one AI).

    updates/README.md and anything under updates/archive/ are ignored."""
    d = root / "updates"
    out = []
    if not d.is_dir():
        return out
    for f in sorted(d.glob("*.md")):
        stem = f.stem.lower()
        if stem == "readme" or (stem in config.MODELS and stem != key):
            continue
        text = f.read_text(encoding="utf-8", errors="replace").strip()
        if text:
            out.append({"file": f"updates/{f.name}", "for": key if stem == key else "everyone", "text": text[:6000]})
    return out


def build(positions, subs, boards=None, root: Optional[Path] = None, key: Optional[str] = None) -> dict:
    ais = config.AI_MODELS
    closed = _closed(positions, ais)
    by_model = {m: _summary([p for p in closed if p.model_key == m]) for m in ais}
    by_book = {b: _summary([p for p in closed if p.bucket == b]) for b in config.BUCKETS}
    by_conf = {c: _summary([p for p in closed if p.confidence == c]) for c in ("high", "medium", "low")}
    widths = {}
    for p in closed:
        w = _stop_width(p)
        if w:
            widths.setdefault(w, []).append(p)
    by_stop = {w: _summary(ps) for w, ps in sorted(widths.items())}
    by_model_book = {m: {b: _summary([p for p in closed if p.model_key == m and p.bucket == b])
                         for b in config.BUCKETS} for m in ais}

    ranked = sorted(closed, key=lambda p: p.ret(), reverse=True)
    recent = sorted(closed, key=lambda p: (p.exit_date, p.id), reverse=True)[:60]
    winners = [_example(p) for p in sorted(recent, key=lambda p: p.ret(), reverse=True)[:6]]
    losers = [_example(p) for p in sorted(recent, key=lambda p: p.ret())[:6]]

    peer = []
    seen: dict[str, int] = {}
    for s in sorted(subs, key=lambda s: s.received_at, reverse=True):
        if s.model_key in ais and s.status in ("ok", "partial") and s.lessons and seen.get(s.model_key, 0) < 3:
            seen[s.model_key] = seen.get(s.model_key, 0) + 1
            peer.append({"model": s.model_key, "night": s.run_date.isoformat(), "lessons": list(s.lessons)[:4]})

    base = {m: _summary(_closed(positions, (m,))) for m in ("fly", "momentum", "learner")}
    return {
        "how_to_use": [
            "Read peer_lessons, winners and losers first. Borrow what worked, and say in your own lessons what you changed because of it.",
            f"A pattern with fewer than {MIN_N} closed trades (reliable=false) is noise. Don't change your strategy because of it.",
            "If your results don't beat the Fruit Fly (random) and Momentum baselines over many trades, your research is not adding value yet. Say so in your lessons.",
            "Never copy another AI's pick just because it won; check the facts and the price yourself.",
        ],
        "closed_trades_total": len(closed),
        "by_model": by_model, "by_book": by_book, "by_model_and_book": by_model_book,
        "by_confidence": by_conf, "by_stop_width": by_stop,
        "recent_winners": winners, "recent_losers": losers, "peer_lessons": peer,
        "baselines": base,
        "operator_updates": read_updates(root, key) if root else [],
    }


def to_markdown(pb: dict) -> str:
    pct = lambda v: "n/a" if v is None else f"{v * 100:+.1f}%"
    lines = ["# Shared playbook", "",
             "Auto-generated after every scoring run. Every AI reads this before it picks.", "",
             f"Closed AI trades so far: **{pb['closed_trades_total']}**. Patterns with fewer than {MIN_N} trades are noise.", "",
             "## Results by AI", "", "| AI | Trades | Avg return | Win rate | Vs S&P | Stopped out |", "|---|---|---|---|---|---|"]
    for m, s in pb["by_model"].items():
        lines.append(f"| {m} | {s['n']} | {pct(s['avg_return'])} | {pct(s['win_rate']).lstrip('+')} | {pct(s['avg_vs_spy'])} | {pct(s['stop_rate']).lstrip('+')} |")
    lines += ["", "## By book, confidence and stop width", "", "| Group | Trades | Avg return | Win rate | Reliable? |", "|---|---|---|---|---|"]
    for title, d in (("book", pb["by_book"]), ("confidence", pb["by_confidence"]), ("stop", pb["by_stop_width"])):
        for k, s in d.items():
            lines.append(f"| {title}: {k} | {s['n']} | {pct(s['avg_return'])} | {pct(s['win_rate']).lstrip('+')} | {'yes' if s['reliable'] else 'no (too few)'} |")
    lines += ["", "## Baselines (luck and simple rules)", ""]
    for m, s in pb["baselines"].items():
        lines.append(f"- **{m}**: {s['n']} trades, avg {pct(s['avg_return'])}, win rate {pct(s['win_rate']).lstrip('+')}")
    for title, key in (("Recent winners", "recent_winners"), ("Recent losers", "recent_losers")):
        lines += ["", f"## {title}", ""]
        for e in pb[key]:
            lines.append(f"- **{e['ticker']}** ({e['model']}, {e['book']}, {e['confidence']} confidence) {pct(e['return'])}, exit: {e['exit']}. {e['thesis']}")
    lines += ["", "## What the AIs told each other", ""]
    for p in pb["peer_lessons"]:
        lines.append(f"**{p['model']}** ({p['night']})")
        lines += [f"- {l}" for l in p["lessons"]]
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
