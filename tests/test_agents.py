import datetime as dt
import json
import unittest
from zoneinfo import ZoneInfo

import numpy as np

from arena import agents, engine
from arena.db import Position, Submission, connect
from arena.prices import Bar, FakeProvider

ET = ZoneInfo("America/New_York")
d = dt.date
MON, TUE, WED = d(2026, 10, 5), d(2026, 10, 6), d(2026, 10, 7)


def at(day, h, m=0):
    return dt.datetime.combine(day, dt.time(h, m), ET)


class WindowTests(unittest.TestCase):
    def test_pick_window(self):
        self.assertEqual(agents.pick_window(at(TUE, 22)), (TUE, TUE, WED))
        self.assertEqual(agents.pick_window(at(WED, 8)), (TUE, TUE, WED))
        self.assertIsNone(agents.pick_window(at(WED, 12)))  # market open: too late to pick for today
        self.assertIsNone(agents.pick_window(at(d(2026, 10, 9), 22)))  # Friday night
        self.assertIsNone(agents.pick_window(at(d(2026, 10, 10), 12)))  # Saturday
        self.assertEqual(agents.pick_window(at(d(2026, 10, 11), 20)), (d(2026, 10, 11), d(2026, 10, 9), d(2026, 10, 12)))
        self.assertEqual(agents.pick_window(at(d(2026, 10, 12), 9)), (d(2026, 10, 11), d(2026, 10, 9), d(2026, 10, 12)))


class BrainTests(unittest.TestCase):
    def test_learns_a_planted_edge_and_surprise_shrinks(self):
        rng = np.random.default_rng(0)
        brain, rpes = agents.Brain(), []
        for i in range(300):
            x = np.zeros(len(agents.FEATURES))
            src = i % 3
            x[src] = 1  # which AI
            x[3 + (i // 3) % 3] = 1  # which book
            edge = {0: -0.01, 1: 0.0, 2: 0.04}[src]  # Grok's picks secretly beat the market by 4%
            rpes.append(abs(brain.learn(x, edge + rng.normal(0, 0.03))))
        w = brain.mean
        self.assertGreater(w[2], w[0] + 0.03)
        self.assertLess(np.mean(rpes[-50:]), np.mean(rpes[:20]))  # less surprised once it has learned


class LearnerTests(unittest.TestCase):
    def setUp(self):
        self.db = connect("sqlite://")()
        self.provider = FakeProvider()

    def add_closed(self, model, bucket, ret, n, day):
        sub = Submission(model_key=model, path=f"inbox/{model}/x", sha=f"{model}{bucket}{ret}{day}", run_date=day,
                         ref_date=day, target_date=day, status="ok", raw="")
        self.db.add(sub)
        for i in range(n):
            sub.positions.append(Position(
                model_key=model, bucket=bucket, ticker=f"{model[:2].upper()}{i}", horizon_days=3, orig_target=110,
                orig_stop=95, target=110, stop=95, entry_date=day, first_session=day, entry_price=100,
                status="closed", exit_date=day, exit_price=100 * (1 + ret), exit_reason="time", sessions_held=2,
                benchmark_entry=100, benchmark_exit=100, confidence="medium"))

    def add_candidates(self, model, n, run, target):
        sub = Submission(model_key=model, path=f"inbox/{model}/{run}", sha=f"c{model}", run_date=run, ref_date=run,
                         target_date=target, status="ok", raw="")
        self.db.add(sub)
        for i in range(n):
            sub.positions.append(Position(
                model_key=model, bucket="catalyst", ticker=f"N{model[:2].upper()}{i}", horizon_days=3,
                orig_target=110, orig_stop=95, target=110, stop=95, entry_date=run, first_session=target,
                ref_price=100, status="open", confidence="medium"))

    def test_learner_copies_the_ai_that_has_been_winning(self):
        for k, day in enumerate([d(2026, 9, 21), d(2026, 9, 28)]):
            self.add_closed("grok", "catalyst", 0.06, 15, day)
            self.add_closed("claude", "catalyst", -0.05, 15, day)
            self.add_closed("chatgpt", "catalyst", -0.01, 15, day)
        self.add_candidates("grok", 4, TUE, WED)
        self.add_candidates("claude", 4, TUE, WED)
        self.add_candidates("chatgpt", 4, TUE, WED)
        self.db.commit()
        out = agents.run_learner(self.db, at(TUE, 22))
        self.assertEqual(out["learner"], "picked")
        mine = self.db.query(Position).filter_by(model_key="learner").all()
        self.assertTrue(mine)
        tickers = [p.ticker for p in mine]
        self.assertEqual(sum(t.startswith("NGR") for t in tickers), 4, tickers)  # every pick from the winner
        self.assertFalse(any(t.startswith("NCL") for t in tickers), tickers)  # nothing from the clear loser
        self.assertTrue(all(p.source_position_id for p in mine))
        sub = self.db.query(Submission).filter_by(model_key="learner").one()
        self.assertEqual(json.loads(sub.raw)["observations"], 90)
        # Same inputs -> same decision, no duplicate submission
        self.assertEqual(agents.run_learner(self.db, at(TUE, 23))["learner"], "unchanged")
        state = agents.learner_state(self.db)
        top = {w["feature"]: w["mean"] for w in state["weights"]}
        self.assertGreater(top["Picked by Grok"], top["Picked by Claude"])
        self.assertEqual(len(state["recent"]), 20)

    def test_no_candidates_no_picks(self):
        self.assertEqual(agents.run_learner(self.db, at(TUE, 22))["learner"], "no AI picks yet")


class FlyTests(unittest.TestCase):
    def test_fly_picks_once_per_night(self):
        db = connect("sqlite://")()
        out = agents.run_fly(db, FakeProvider(), at(MON, 22))
        self.assertEqual(out["picks"], 15)
        picks = db.query(Position).filter_by(model_key="fly").all()
        self.assertEqual(sorted({p.bucket for p in picks}), ["catalyst", "compounder", "moonshot"])
        self.assertTrue(all(p.ref_price for p in picks))
        p = picks[0]
        self.assertAlmostEqual(p.orig_target / p.ref_price, 1.10, places=2)
        self.assertEqual(agents.run_fly(db, FakeProvider(), at(MON, 23))["fly"], "already picked")
        # Next night the compounder book is already full
        engine.score(db, FakeProvider(), now=at(TUE, 16, 30), with_intraday=False)
        agents.run_fly(db, FakeProvider(), at(TUE, 22))
        comps = db.query(Position).filter_by(model_key="fly", bucket="compounder", status="open").count()
        self.assertLessEqual(comps, 5)


class MirrorTests(unittest.TestCase):
    def test_learner_copy_follows_the_source_ai_sell(self):
        bars = {}
        p = FakeProvider(overrides=bars)
        for day in [MON - dt.timedelta(days=i) for i in range(40)] + [MON, TUE, WED]:
            bars[("AAA", day)] = Bar(100, 101, 99, 100, 2e6)
            bars[("SPY", day)] = Bar(100, 101, 99, 100, 2e6)
        bars[("AAA", WED)] = Bar(104, 105, 103, 104, 2e6)
        db = connect("sqlite://")()
        raw = json.dumps({"compounder": [{"ticker": "AAA", "target_price": 150, "stop_price": 80}]})
        engine.ingest(db, p, "claude", "inbox/claude/x.json", MON.isoformat(), raw, at(MON, 20, 45))
        src = db.query(Position).filter_by(model_key="claude").one()
        sub = Submission(model_key="learner", path="internal", sha="l", run_date=MON, ref_date=MON,
                         target_date=TUE, status="ok", raw="")
        db.add(sub)
        sub.positions.append(Position(model_key="learner", bucket="compounder", ticker="AAA", horizon_days=60,
                                      orig_target=150, orig_stop=80, target=150, stop=80, entry_date=MON,
                                      first_session=TUE, ref_price=100, source_position_id=src.id))
        db.commit()
        engine.score(db, p, now=at(TUE, 16, 30), with_intraday=False)
        engine.ingest(db, p, "claude", "inbox/claude/y.json", TUE.isoformat(),
                      json.dumps({"review": [{"position_id": src.id, "action": "SELL"}]}), at(TUE, 20, 45))
        db.commit()
        engine.score(db, p, now=at(WED, 16, 30), with_intraday=False)
        copy = db.query(Position).filter_by(model_key="learner").one()
        self.assertEqual((copy.exit_reason, copy.exit_price), ("model_sell", 104))


if __name__ == "__main__":
    unittest.main()
