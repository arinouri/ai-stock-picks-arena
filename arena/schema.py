"""Parse and validate the JSON file a bot submits. Forgiving about formatting, strict about content."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from . import config

TICKER_RE = re.compile(r"^[A-Z]{1,5}(?:[.\-][A-Z]{1,2})?$")
FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)
URL_RE = re.compile(r"^https?://\S+$")


@dataclass
class PickIn:
    bucket: str
    ticker: str
    thesis: str = ""
    catalyst_time: str = ""
    entry_zone_low: Optional[float] = None
    entry_zone_high: Optional[float] = None
    target_price: Optional[float] = None
    stop_price: Optional[float] = None
    horizon_days: int = 1
    confidence: str = "medium"
    main_risk: str = ""
    sources: list = field(default_factory=list)


@dataclass
class ReviewIn:
    position_id: int
    ticker: str
    action: str
    reason: str = ""
    new_stop: Optional[float] = None
    new_target: Optional[float] = None


@dataclass
class SubmissionIn:
    model: str = ""
    model_version: str = ""
    market_view: str = ""
    lessons: list = field(default_factory=list)
    picks: list[PickIn] = field(default_factory=list)
    reviews: list[ReviewIn] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- helpers


def extract_json(text: str) -> Any:
    """First JSON object/array in text (tolerates ```json fences and prose around it)."""
    if not text or not text.strip():
        raise ValueError("file is empty")
    decoder = json.JSONDecoder()
    for cand in [m.group(1) for m in FENCE_RE.finditer(text)] + [text]:
        cand = cand.strip().lstrip("﻿")
        try:
            return json.loads(cand)
        except json.JSONDecodeError:
            pass
        for i, ch in enumerate(cand):
            if ch in "{[":
                try:
                    return decoder.raw_decode(cand[i:])[0]
                except json.JSONDecodeError:
                    continue
    raise ValueError("no valid JSON found")


def num(v: Any) -> Optional[float]:
    if v is None or v == "" or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v) if v == v else None
    if isinstance(v, str):
        m = re.search(r"-?\d+(?:,\d{3})*(?:\.\d+)?", v.replace("$", ""))
        if m:
            return float(m.group(0).replace(",", ""))
    return None


def text(v: Any, limit: int = 600) -> str:
    return "" if v is None else str(v).strip()[:limit]


def clean_ticker(v: Any) -> str:
    t = text(v, 24).upper().replace("$", "").strip()
    if ":" in t:
        t = t.split(":")[-1].strip()
    return t


def _lower_keys(d: dict) -> dict:
    return {str(k).lower().strip().replace(" ", "_"): v for k, v in d.items()}


# --------------------------------------------------------------------------- parse

BUCKET_ALIASES = {
    "moonshot": "moonshot", "moonshots": "moonshot", "high_risk": "moonshot", "high_risk_high_reward": "moonshot",
    "catalyst": "catalyst", "catalysts": "catalyst", "news": "catalyst", "research": "catalyst",
    "compounder": "compounder", "compounders": "compounder", "long_term": "compounder",
}


def parse_submission(raw: str) -> SubmissionIn:
    out = SubmissionIn()
    try:
        data = extract_json(raw)
    except ValueError as e:
        out.errors.append(str(e))
        return out
    if not isinstance(data, dict):
        out.errors.append("top level must be a JSON object with moonshot, catalyst, compounder and review keys")
        return out
    d = _lower_keys(data)
    out.model = text(d.get("model"), 32).lower()
    out.model_version = text(d.get("model_version"), 128)
    out.market_view = text(d.get("market_view"), 1200)
    out.lessons = [text(x, 400) for x in (d.get("lessons") or []) if isinstance(x, (str, int, float)) and text(x)][:3]

    seen: set[tuple[str, str]] = set()
    for key, raw_list in d.items():
        bucket = BUCKET_ALIASES.get(key)
        if bucket is None:
            continue
        if not isinstance(raw_list, list):
            out.errors.append(f"{key} must be a list")
            continue
        for i, item in enumerate(raw_list):
            p = _parse_pick(bucket, i, item, out.errors)
            if p is None:
                continue
            if (bucket, p.ticker) in seen:
                out.errors.append(f"{bucket}: duplicate ticker {p.ticker}")
                continue
            seen.add((bucket, p.ticker))
            out.picks.append(p)

    for i, item in enumerate(d.get("review") or d.get("reviews") or []):
        if not isinstance(item, dict):
            out.errors.append(f"review item {i} is not an object")
            continue
        r = _lower_keys(item)
        pid = num(r.get("position_id") if r.get("position_id") is not None else r.get("id"))
        action = text(r.get("action"), 8).upper()
        if pid is None:
            out.errors.append(f"review item {i} has no position_id")
            continue
        if action not in ("HOLD", "SELL"):
            out.errors.append(f"review for position {int(pid)}: action must be HOLD or SELL")
            continue
        out.reviews.append(ReviewIn(position_id=int(pid), ticker=clean_ticker(r.get("ticker")), action=action,
                                    reason=text(r.get("reason")), new_stop=num(r.get("new_stop")),
                                    new_target=num(r.get("new_target"))))
    return out


def _parse_pick(bucket: str, i: int, item: Any, errors: list[str]) -> Optional[PickIn]:
    if not isinstance(item, dict):
        errors.append(f"{bucket} item {i} is not an object")
        return None
    r = _lower_keys(item)
    ticker = clean_ticker(r.get("ticker") or r.get("symbol"))
    if not TICKER_RE.match(ticker):
        errors.append(f"{bucket} item {i}: invalid ticker {ticker!r}")
        return None
    rule = config.BUCKETS[bucket]
    lo, hi = rule["horizon"]
    h = num(r.get("horizon_days"))
    horizon = int(h) if h is not None else rule["default_horizon"]
    horizon = min(max(horizon, lo), hi)
    conf = text(r.get("confidence"), 10).lower()
    sources = r.get("sources") or []
    if isinstance(sources, str):
        sources = [sources]
    p = PickIn(
        bucket=bucket, ticker=ticker,
        thesis=text(r.get("thesis") or r.get("catalyst") or r.get("reason")),
        catalyst_time=text(r.get("catalyst_time"), 80),
        entry_zone_low=num(r.get("entry_zone_low")), entry_zone_high=num(r.get("entry_zone_high")),
        target_price=num(r.get("target_price") or r.get("target")),
        stop_price=num(r.get("stop_price") or r.get("stop")),
        horizon_days=horizon,
        confidence=conf if conf in ("low", "medium", "high") else "medium",
        main_risk=text(r.get("main_risk") or r.get("risk")),
        sources=[text(s, 400) for s in sources if isinstance(s, str) and URL_RE.match(s.strip())][:4],
    )
    if p.target_price is None or p.stop_price is None:
        errors.append(f"{bucket} {ticker}: target_price and stop_price are required")
        return None
    if p.stop_price >= p.target_price:
        errors.append(f"{bucket} {ticker}: stop_price must be below target_price")
        return None
    return p


if __name__ == "__main__":  # python3 -m arena.schema FILE  (no dependencies needed)
    import sys

    parsed = parse_submission(open(sys.argv[1], encoding="utf-8").read())
    counts = {b: sum(1 for p in parsed.picks if p.bucket == b) for b in config.BUCKETS}
    print(json.dumps({"picks": counts, "reviews": len(parsed.reviews), "lessons": len(parsed.lessons),
                      "problems": parsed.errors}, indent=2))
    sys.exit(1 if parsed.errors else 0)
