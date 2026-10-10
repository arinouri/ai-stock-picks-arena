import datetime as dt
import json
import unittest
from zoneinfo import ZoneInfo

from arena import config, engine
from arena.db import Position, Submission, connect
from arena.prices import Bar, FakeProvider

ET = ZoneInfo("America/New_York")
MON, TUE, WED, THU, FRI = (dt.date(2026, 10, 5 + i) for i in range(5))


def at(day, h, m=0):
    return dt.datetime.combine(day, dt.time(h, m), ET)


def pick(t, target=110, stop=95, **kw):
    d = {"ticker": t, "thesis": "Earnings tonight", "target_price": target, "stop_price": stop,
         "confidence": "high", "sources": ["https://example.com/news"]}
    d.update(kw)
    return d


def sub(moon=(), cat=(), comp=(), review=(), lessons=("Watch the open",)):
    return json.dumps({"model": "claude", "market_view": "Risk-on.", "lessons": list(lessons),
                       "moonshot": list(moon), "catalyst": list(cat), "compounder": list(comp),
                       "review": list(review)})


class EngineBase(unittest.TestCase):
    def setUp(self):
        self._cost, config.COST_PER_SIDE = config.COST_PER_SIDE, 0.0  # costs have their own test
        self.Session = connect("sqlite://")
        self.db = self.Session()
        self.bars = {}
        self.p = FakeProvider(overrides=self.bars)
        # every ticker closes at exactly 100 on Monday with plenty of volume
        for t in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "SPY"]:
            self.bars[(t, MON)] = Bar(100, 101, 99, 100, 2e6)
            for d in (TUE, WED, THU, FRI):
                self.bars.setdefault((t, d), Bar(100, 101, 99, 100, 2e6))
        for d in (MON - dt.timedelta(days=i) for i in range(1, 40)):
            for t in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "SPY"]:
                self.bars[(t, d)] = Bar(100, 101, 99, 100, 2e6)

    def tearDown(self):
        config.COST_PER_SIDE = self._cost
        self.db.close()

    def ingest(self, raw, day=MON, when=None, model="claude", stem=None):
        s = engine.ingest(self.db, self.p, model, f"inbox/{model}/{stem or day}.json", stem or day.isoformat(),
                          raw, when or at(day, 20, 45))
        self.db.commit()
        return s

    def score(self, day, h=16, m=30):
        return engine.score(self.db, self.p, now=at(day, h, m), with_intraday=False)

    def pos(self, ticker):
        return self.db.query(Position).filter_by(ticker=ticker).one()


class IngestTests(EngineBase):
    def test_full_valid_submission(self):
        s = self.ingest(sub(moon=[pick(t) for t in "ABCDE"], cat=[pick(t, horizon_days=3) for t in "FGHIJ"],
                            comp=[pick(t, 150, 80, horizon_days=60) for t in "KLMN"]))
        self.assertEqual(s.status, "ok", s.errors)
        self.assertEqual((s.ref_date, s.target_date), (MON, TUE))
        self.assertEqual(len(s.positions), 14)
        self.assertTrue(all(p.ref_price == 100 for p in s.positions))  # bought later, at the open
        self.assertEqual(self.pos("F").horizon_days, 3)
        self.assertEqual(self.pos("A").horizon_days, 1)  # moonshots are always 1 session

    def test_rule_violations_void_picks(self):
        self.bars[("A", MON)] = Bar(0.8, 0.9, 0.7, 0.8, 2e6)  # under $1
        for d in list(self.bars):
            if d[0] == "B":
                self.bars[d] = Bar(100, 101, 99, 100, 1e5)  # thin volume
        self.p.missing = {"ZZZZ"}  # not a real listing
        s = self.ingest(sub(moon=[pick("A", 1, 0.5), pick("B"), pick("C", target=99, stop=90), pick("ZZZZ"),
                                  pick("D")]))
        self.assertEqual(s.status, "partial")
        statuses = {p.ticker: p.status for p in s.positions}
        self.assertEqual(statuses, {"A": "void", "B": "void", "C": "void", "ZZZZ": "void", "D": "open"})
        joined = " ".join(s.errors)
        self.assertIn("not above $1", joined)
        self.assertIn("under 500K", joined)
        self.assertIn("not above the entry price", joined)
        self.assertIn("no price data", joined)

    def test_late_and_wrong_night(self):
        late = self.ingest(sub(moon=[pick("A")]), when=at(TUE, 0, 30))
        self.assertEqual(late.status, "late")
        self.assertEqual(late.positions, [])
        fri = self.ingest(sub(moon=[pick("A")]), day=FRI, when=at(FRI, 20))
        self.assertEqual(fri.status, "rejected")

    def test_resubmission_replaces_earlier_file(self):
        self.ingest(sub(moon=[pick("A")]))
        second = self.ingest(sub(moon=[pick("B"), pick("C")]), when=at(MON, 21))
        self.assertEqual(second.status, "partial")  # fewer than 5 moonshots
        self.assertEqual(self.db.query(Submission).filter_by(status="superseded").count(), 1)
        self.assertEqual(sorted(p.ticker for p in self.db.query(Position)), ["B", "C"])

    def test_same_file_twice_is_ignored(self):
        raw = sub(moon=[pick("A")])
        self.assertIsNotNone(self.ingest(raw))
        self.assertIsNone(self.ingest(raw))

    def test_compounder_book_capacity_counts_sells(self):
        self.ingest(sub(comp=[pick(t, 150, 80, horizon_days=60) for t in "ABCDE"]))
        self.score(TUE)
        ids = {p.ticker: p.id for p in self.db.query(Position)}
        s = self.ingest(sub(comp=[pick("F", 150, 80), pick("G", 150, 80)],
                            review=[{"position_id": ids["A"], "action": "SELL", "reason": "thesis broke"}]),
                        day=TUE)
        self.assertEqual(sorted(p.ticker for p in s.positions), ["F"])
        self.assertTrue(any("max 5" in e for e in s.errors))

    def test_garbage_file(self):
        s = self.ingest("I couldn't find anything today, sorry!")
        self.assertEqual(s.status, "rejected")


class ExitRuleTests(EngineBase):
    def open_one(self, bucket="catalyst", horizon=3, target=110, stop=95):
        kw = {bucket: [pick("A", target, stop, horizon_days=horizon)]}
        self.ingest(sub(moon=kw.get("moonshot", []), cat=kw.get("catalyst", []), comp=kw.get("compounder", [])))
        return self.pos("A")

    def test_target_hit(self):
        self.bars[("A", TUE)] = Bar(100, 112, 100, 108)
        p = self.open_one()
        self.score(TUE)
        self.assertEqual((p.status, p.exit_reason, p.exit_price), ("closed", "target", 110))
        self.assertAlmostEqual(p.pnl(), 10.0)
        self.assertTrue(p.d1()["boom"])

    def test_both_hit_counts_as_stop(self):
        self.bars[("A", TUE)] = Bar(100, 120, 90, 105)
        p = self.open_one()
        self.score(TUE)
        self.assertEqual((p.exit_reason, p.exit_price), ("stop", 95))
        self.assertTrue(p.d1()["hit_stop"])
        self.assertFalse(p.d1()["hit_target"])

    def test_gap_down_exits_at_open(self):
        self.bars[("A", WED)] = Bar(80, 85, 78, 82)
        p = self.open_one()
        self.score(TUE)
        self.score(WED)
        self.assertEqual((p.exit_reason, p.exit_price), ("stop", 80))
        self.assertAlmostEqual(p.pnl(), -20.0)

    def test_gap_up_through_target_exits_at_open(self):
        self.bars[("A", TUE)] = Bar(130, 135, 125, 128)
        p = self.open_one()
        self.score(TUE)
        self.assertEqual((p.exit_reason, p.exit_price), ("target", 130))

    def test_bought_at_next_open_and_costs_charged(self):
        config.COST_PER_SIDE = 0.001
        self.bars[("A", TUE)] = Bar(104, 108, 103, 106)  # gaps up on the news: the buy is at 104, not Monday's 100
        p = self.open_one("moonshot", 1)
        self.assertEqual((p.ref_price, p.entry_price), (100, None))
        self.score(TUE)
        self.assertEqual(p.entry_price, 104)
        self.assertAlmostEqual(p.ret(), 106 / 104 - 1 - 0.002)
        self.assertAlmostEqual(sum(d.pnl for d in p.days), p.pnl())

    def test_moonshot_exits_at_first_close(self):
        self.bars[("A", TUE)] = Bar(100, 104, 98, 103)
        p = self.open_one("moonshot", 1)
        self.score(TUE)
        self.assertEqual((p.exit_reason, p.exit_price, p.sessions_held), ("time", 103, 1))

    def test_time_stop_after_horizon_and_daily_marks(self):
        self.bars[("A", TUE)] = Bar(100, 104, 99, 102)
        self.bars[("A", WED)] = Bar(102, 105, 101, 104)
        self.bars[("A", THU)] = Bar(104, 106, 100, 101)
        p = self.open_one("catalyst", 3)
        self.score(TUE)
        self.assertEqual((p.status, p.last_price), ("open", 102))
        self.score(THU)  # catches up WED and THU in one run
        self.assertEqual((p.exit_reason, p.exit_date, p.exit_price), ("time", THU, 101))
        self.assertEqual([d.mark for d in p.days], [102, 104, 101])
        self.assertAlmostEqual(sum(d.pnl for d in p.days), p.pnl())

    def test_model_sell_exits_next_open_and_moves_levels(self):
        self.bars[("A", TUE)] = Bar(100, 104, 99, 103)
        self.bars[("A", WED)] = Bar(104, 107, 103, 106)
        p = self.open_one("compounder", 60, 150, 80)
        self.score(TUE)
        self.ingest(sub(review=[{"position_id": p.id, "action": "HOLD", "new_stop": 101}]), day=TUE)
        self.score(WED)
        self.assertEqual(p.stop, 101)
        self.assertEqual(p.status, "open")
        self.bars[("A", THU)] = Bar(105, 106, 104, 105)
        self.ingest(sub(review=[{"position_id": p.id, "action": "SELL", "reason": "valuation"}]), day=WED)
        self.assertEqual(p.sell_at_open_on, THU)
        self.score(THU)
        self.assertEqual((p.exit_reason, p.exit_price, p.exit_date), ("model_sell", 105, THU))

    def test_review_of_unknown_position(self):
        s = self.ingest(sub(review=[{"position_id": 999, "action": "SELL"}]))
        self.assertTrue(any("not one of your open positions" in e for e in s.errors))

    def test_no_scoring_before_close(self):
        self.open_one()
        self.score(TUE, 15, 0)
        self.assertEqual(self.pos("A").sessions_held, 0)

    def test_weekend_run_skips_inverted_provider_range_when_current(self):
        self.open_one("compounder", 60, 150, 80)
        self.score(FRI)
        original = self.p.daily_bars

        def reject_inverted(tickers, start, end):
            self.assertLessEqual(start, end)
            return original(tickers, start, end)

        self.p.daily_bars = reject_inverted
        result = self.score(dt.date(2026, 10, 10))
        self.assertEqual(result["processed_sessions"], 0)
        self.assertEqual(result["last_session"], FRI.isoformat())

    def test_missing_data_voids_after_five_sessions(self):
        p = self.open_one()
        for d in (TUE, WED, THU, FRI):
            del self.bars[("A", d)]
        self.p.missing = set()
        self.p.daily_bars_orig = self.p.daily_bars
        orig = self.p.daily_bars
        self.p.daily_bars = lambda tickers, s, e: {t: {d: b for d, b in v.items() if not (t == "A" and d > MON)}
                                                   for t, v in orig(tickers, s, e).items()}
        self.score(dt.date(2026, 10, 12))
        self.assertEqual(p.status, "void")


if __name__ == "__main__":
    unittest.main()


class ExportTests(EngineBase):
    def test_export_writes_site_and_briefings(self):
        import tempfile
        from pathlib import Path

        from arena.export import export_site

        self.bars[("A", TUE)] = Bar(100, 112, 100, 108)
        self.ingest(sub(moon=[pick("A")], cat=[pick("B", horizon_days=3)], comp=[pick("C", 150, 80)]))
        self.score(TUE)
        with tempfile.TemporaryDirectory() as tmp:
            export_site(self.db, Path(tmp), now=at(TUE, 18))
            dash = json.loads((Path(tmp) / "data" / "dashboard.json").read_text())
            brief = json.loads((Path(tmp) / "data" / "brief" / "claude.json").read_text())
            self.assertEqual(dash["session"]["date"], TUE.isoformat())
            self.assertEqual(dash["boards"]["all"]["moonshot"][0]["model"], "claude")
            self.assertAlmostEqual(dash["boards"]["all"]["moonshot"][0]["total_pnl"], 10.0)
            self.assertEqual({p["ticker"] for p in brief["open_positions"]}, {"B", "C"})
            self.assertEqual(brief["tonight"]["upload_path"], f"inbox/claude/{TUE}.json")
            self.assertEqual(brief["compounder_slots_free"], 4)
            self.assertTrue((Path(tmp) / "data" / "export.csv").read_text().startswith("id,model"))
            self.assertIn("out_of_sample", dash["evaluation"]["learner"])
            self.assertIn("portfolios", dash)
            self.assertIn("health", dash)
