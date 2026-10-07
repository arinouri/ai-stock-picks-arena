"""Command line.

  python -m arena.cli run                 ingest new inbox files, score closed sessions, rebuild site data
  python -m arena.cli ingest | score | export
  python -m arena.cli validate FILE       check a submission file without saving anything
  python -m arena.cli demo [--days 30]    build the site from fake bots + fake prices (data/demo.db)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import random
import subprocess
import sys
from pathlib import Path

from . import config
from .db import Position, Submission, connect
from .engine import ET, ingest, ingest_file, now_et, score, sha256
from .export import export_site
from .market_calendar import session_plan, should_run_picks_tonight
from .prices import FakeProvider, get_provider
from .agents import run_fly, run_learner
from .schema import parse_submission

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("arena")


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True, check=True, cwd=config.ROOT).stdout.strip()
    except Exception:
        return ""


def inbox_files(inbox: Path) -> list[Path]:
    files = [p for p in inbox.glob("*/*.json") if p.parent.name in config.AI_MODELS]

    def order(p: Path):
        ct = _git("log", "-1", "--format=%ct", "--", str(p))
        return (int(ct) if ct.isdigit() else int(p.stat().st_mtime), str(p))

    return sorted(files, key=order)


def cmd_ingest(Session, provider, now) -> list:
    out = []
    with Session() as db:
        known = {(s.path, s.sha) for s in db.query(Submission.path, Submission.sha)}
        for path in inbox_files(config.INBOX_DIR):
            rel = str(Path("inbox") / path.relative_to(config.INBOX_DIR))
            if (rel, sha256(path.read_text(encoding="utf-8", errors="replace"))) in known:
                continue
            author = _git("log", "-1", "--format=%an <%ae>", "--", str(path))
            sub = ingest_file(db, provider, path, config.INBOX_DIR, now, author)
            if sub is not None:
                db.commit()
                log.info("%s -> %s %s", rel, sub.status, "; ".join(sub.errors or [])[:300])
                out.append(sub)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m arena.cli")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "ingest", "score", "export", "prompts"):
        sub.add_parser(name)
    v = sub.add_parser("validate")
    v.add_argument("file")
    d = sub.add_parser("demo")
    d.add_argument("--days", type=int, default=30)
    args = ap.parse_args(argv)

    if args.cmd == "validate":
        parsed = parse_submission(Path(args.file).read_text())
        counts = {b: sum(1 for p in parsed.picks if p.bucket == b) for b in config.BUCKETS}
        print(json.dumps({"picks": counts, "reviews": len(parsed.reviews), "lessons": len(parsed.lessons),
                          "problems": parsed.errors}, indent=2))
        return 1 if parsed.errors else 0
    if args.cmd == "demo":
        return demo(args.days)
    if args.cmd == "prompts":
        return build_prompts()

    Session = connect()
    provider = get_provider()
    now = now_et()
    if args.cmd in ("run", "ingest"):
        cmd_ingest(Session, provider, now)
    if args.cmd in ("run", "score"):
        with Session() as db:
            log.info("score: %s", score(db, provider, now))
    if args.cmd == "run":
        with Session() as db:
            log.info("fly: %s", run_fly(db, provider, now))
            log.info("learner: %s", run_learner(db, now))
    if args.cmd in ("run", "export"):
        with Session() as db:
            log.info("export: %s", export_site(db, now=now, brief_dir=config.ROOT / "brief"))
    return 0


def build_prompts() -> int:
    """prompts/ready/<model>.md = nightly prompt + that bot's upload section, ready to paste."""
    pdir = config.ROOT / "prompts"
    nightly = (pdir / "nightly-prompt.md").read_text().split("\n---\n", 1)[1].strip()
    setups = {"claude": "setup-claude.md", "chatgpt": "setup-chatgpt.md", "grok": "setup-grok-bot.md"}
    (pdir / "ready").mkdir(exist_ok=True)
    for key, fname in setups.items():
        setup = (pdir / fname).read_text()
        upload = setup.split("\n---\n", 1)[1].split("\n## ", 1)[0].strip()
        name = config.MODELS[key]["display_name"]
        text = nightly.replace("{NAME}", name).replace("{KEY}", key) + "\n\n" + upload + "\n"
        (pdir / "ready" / f"{key}.md").write_text(text)
        print(f"wrote prompts/ready/{key}.md ({len(text)} chars)")
    return 0


# =========================================================================== demo

DEMO_UNIVERSE = [
    "NVDA", "AMD", "PLTR", "SMCI", "TSLA", "SOFI", "RIVN", "MRNA", "CRWD", "SNOW", "SHOP", "COIN", "MSTR", "HOOD",
    "AFRM", "UPST", "DKNG", "ROKU", "NET", "DDOG", "MDB", "ZS", "PANW", "ARM", "MU", "AVGO", "ORCL", "UBER", "PINS",
    "RBLX", "IONQ", "RKLB", "ASTS", "HIMS", "CELH", "ENPH", "FSLR", "LLY", "VKTX", "CRSP", "MSFT", "AAPL", "AMZN",
    "GOOGL", "META", "COST", "V", "MA", "ASML", "TSM", "NOW", "INTU", "ISRG", "SPGI", "UNH", "JPM", "BRK.B",
]
COMPOUNDERS = ["MSFT", "AAPL", "AMZN", "GOOGL", "META", "COST", "V", "MA", "ASML", "TSM", "NOW", "INTU", "ISRG",
               "SPGI", "LLY", "AVGO", "BRK.B", "JPM", "UNH", "ORCL"]
THESES = {
    "moonshot": ["Reports after the close; options imply a double-digit move and short interest is high.",
                 "FDA decision due before the open; a yes could re-rate the whole pipeline.",
                 "Unusual call buying into a rumored partnership announcement.",
                 "Added to a major index at tomorrow's open with heavy forced buying."],
    "catalyst": ["Beat-and-raise last night; analysts are still catching up on estimates.",
                 "Investor day this week with new long-term margin targets expected.",
                 "Two upgrades today and the sector is turning; room to run for a few sessions.",
                 "Phase 3 data at a conference Thursday; setup favors a run-up into it."],
    "compounder": ["Dominant platform with 20%+ revenue growth and expanding margins.",
                   "Pricing power and recurring revenue; buying on a pullback to the 50-day.",
                   "Wide moat, buybacks, and AI demand that is still early."],
}
VIEWS = ["Breadth is improving and small caps lead; leaning into risk.",
         "Rates backed up again; staying selective and keeping stops tight.",
         "Heavy earnings week; volatility is the opportunity, sizing matters.",
         "Index at highs on narrow leadership; favoring catalysts over momentum."]
LESSONS = ["Earnings plays with raised guidance held up; pure hype names faded.",
           "Stops under 5% were too tight for biotech; give them more room.",
           "Gap-ups at the open mostly faded; better entries come after 10 AM.",
           "Index-inclusion trades moved less than expected; lower their weight.",
           "High-confidence picks beat low-confidence ones; trust conviction more.",
           "Targets above +15% were rarely hit in one session; be more realistic."]


def demo(days: int) -> int:
    db_path = config.ROOT / "data" / "demo.db"
    if db_path.exists():
        db_path.unlink()
    Session = connect(f"sqlite:///{db_path}")
    provider = FakeProvider()
    today = now_et().date()
    nights, d = [], today - dt.timedelta(days=1)
    while len(nights) < days:
        if should_run_picks_tonight(d):
            nights.append(d)
        d -= dt.timedelta(days=1)
    with Session() as db:
        for night in sorted(nights):
            ref, target = session_plan(night)
            for k in config.AI_MODELS:
                rng = random.Random(f"{k}{night}")
                raw = json.dumps(_fake_submission(db, rng, k, provider, ref))
                ingest(db, provider, k, f"inbox/{k}/{night}.json", night.isoformat(), raw,
                       dt.datetime.combine(night, dt.time(20, 45), ET), author=f"{k}-bot")
                db.commit()
            agent_time = dt.datetime.combine(night, dt.time(22, 0), ET)
            run_fly(db, provider, agent_time)
            run_learner(db, agent_time)
            if target < today:
                score(db, provider, now=dt.datetime.combine(target, dt.time(16, 30), ET), with_intraday=True)
        export_site(db)
    print(f"Demo site data written to {config.SITE_DIR / 'data'} from {len(nights)} fake nights.")
    print("Preview: python -m http.server 8000 --directory site   then open http://localhost:8000")
    return 0


def _fake_submission(db, rng, key, provider, ref):
    open_pos = db.query(Position).filter_by(model_key=key, status="open").all()
    review, selling = [], set()
    for p in open_pos:
        if p.entry_price is None or p.first_session > ref + dt.timedelta(days=4):
            continue
        r = (p.last_price or p.entry_price) / p.entry_price - 1
        if p.bucket != "moonshot" and rng.random() < (0.12 if r < 0 else 0.05):
            review.append({"position_id": p.id, "ticker": p.ticker, "action": "SELL",
                           "reason": "Thesis isn't playing out; freeing the slot." if r < 0 else "Taking profits into strength."})
            selling.add(p.id)
        elif p.bucket != "moonshot":
            item = {"position_id": p.id, "ticker": p.ticker, "action": "HOLD", "reason": "Thesis intact."}
            if r > 0.06:
                item["new_stop"] = round(p.entry_price * 1.01, 2)
                item["reason"] = "Working; moving the stop above entry."
            review.append(item)

    def mk(bucket, t, up, down, horizon):
        price = round(provider._close(t, ref), 2)
        return {"ticker": t, "thesis": rng.choice(THESES[bucket]), "catalyst_time": rng.choice(
            ["after close", "before open", "8:00 AM ET", "this week"]),
            "entry_zone_low": round(price * 0.99, 2), "entry_zone_high": round(price * 1.01, 2),
            "target_price": round(price * up, 2), "stop_price": round(price * down, 2), "horizon_days": horizon,
            "confidence": rng.choice(["low", "medium", "high"]), "main_risk": "Catalyst disappoints or the market sells off.",
            "sources": ["https://example.com/demo-source"]}

    pool = [t for t in DEMO_UNIVERSE if t not in COMPOUNDERS[:8]]
    moon = rng.sample(pool, 5)
    cat = rng.sample([t for t in pool if t not in moon], 5)
    held = {p.ticker for p in open_pos if p.bucket == "compounder" and p.id not in selling}
    free = 5 - len(held)
    comp = rng.sample([t for t in COMPOUNDERS if t not in held], free) if free > 0 else []
    return {
        "model": key, "model_version": f"demo-{key}", "market_view": rng.choice(VIEWS),
        "lessons": rng.sample(LESSONS, 2), "review": review,
        "moonshot": [mk("moonshot", t, rng.uniform(1.06, 1.16), rng.uniform(0.92, 0.96), 1) for t in moon],
        "catalyst": [mk("catalyst", t, rng.uniform(1.08, 1.2), rng.uniform(0.9, 0.95), rng.randint(2, 5)) for t in cat],
        "compounder": [mk("compounder", t, rng.uniform(1.25, 1.5), rng.uniform(0.8, 0.88), rng.randint(40, 90)) for t in comp],
    }


if __name__ == "__main__":
    sys.exit(main())
