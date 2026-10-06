import datetime as dt
import json
import unittest

from arena.schema import parse_submission
from arena.stats import Day, Trade, board, equity_curve, session_summary, session_winners

D1, D2 = dt.date(2026, 10, 6), dt.date(2026, 10, 7)


class SchemaTests(unittest.TestCase):
    def test_parses_all_sections_and_aliases(self):
        raw = "Here you go:\n```json\n" + json.dumps({
            "Model": "grok", "market_view": "ok", "lessons": ["one", "two", "three", "four"],
            "moonshots": [{"ticker": "NASDAQ:$nvda", "catalyst": "earnings", "target_price": "$1,200.50",
                           "stop_price": "1,000", "confidence": "HIGH", "sources": ["https://a.com", "not a url"]}],
            "catalyst": [{"symbol": "AMD", "thesis": "x", "target": 200, "stop": 150, "horizon_days": 12}],
            "compounders": [{"ticker": "BRK.B", "target_price": 600, "stop_price": 400}],
            "review": [{"position_id": "7", "action": "sell", "reason": "done"}],
        }) + "\n```"
        s = parse_submission(raw)
        self.assertEqual(s.errors, [])
        self.assertEqual(s.model, "grok")
        self.assertEqual(len(s.lessons), 3)
        moon, cat, comp = s.picks
        self.assertEqual((moon.ticker, moon.target_price, moon.stop_price, moon.confidence, moon.horizon_days),
                         ("NVDA", 1200.5, 1000.0, "high", 1))
        self.assertEqual(moon.sources, ["https://a.com"])
        self.assertEqual(cat.horizon_days, 5)  # clamped to the 1-5 catalyst range
        self.assertEqual(comp.horizon_days, 60)  # default
        self.assertEqual((s.reviews[0].position_id, s.reviews[0].action), (7, "SELL"))

    def test_bad_items_reported(self):
        s = parse_submission(json.dumps({"moonshot": [{"ticker": "toolongticker", "target_price": 1, "stop_price": 0.5},
                                                      {"ticker": "A", "target_price": 5},
                                                      {"ticker": "B", "target_price": 5, "stop_price": 6},
                                                      {"ticker": "C", "target_price": 5, "stop_price": 4},
                                                      {"ticker": "C", "target_price": 5, "stop_price": 4}],
                                         "review": [{"action": "HOLD"}, {"position_id": 3, "action": "BUY"}]}))
        self.assertEqual([p.ticker for p in s.picks], ["C"])
        self.assertEqual(len(s.errors), 6)

    def test_not_json(self):
        self.assertTrue(parse_submission("no picks today").errors)
        self.assertTrue(parse_submission("[1, 2]").errors)


def t(id, model, bucket, ret, status="closed", reason="time", day=D1, bench=0.0, d1=None):
    return Trade(id, model, bucket, f"T{id}", day, status, ret, reason, 2, bench, d1 or {})


class StatsTests(unittest.TestCase):
    def setUp(self):
        self.trades = [
            t(1, "claude", "moonshot", 0.10, reason="target", d1={"pct_to_close": 0.08, "boom": True, "hit_target": True}),
            t(2, "claude", "moonshot", -0.05, reason="stop", d1={"pct_to_close": -0.05, "boom": False}),
            t(3, "claude", "compounder", 0.02, status="open", reason=None, day=D2),
            t(4, "grok", "catalyst", 0.04, bench=0.01),
            t(5, "grok", "catalyst", None, status="open"),  # entry not filled yet: ignored
        ]
        self.days = [Day("claude", "moonshot", D1, 10.0, 1), Day("claude", "moonshot", D1, -5.0, 2),
                     Day("claude", "compounder", D2, 2.0, 3), Day("grok", "catalyst", D1, 1.0, 4),
                     Day("grok", "catalyst", D2, 3.0, 4)]

    def test_board_all(self):
        rows = {r["model"]: r for r in board(self.trades, self.days, ["claude", "grok", "chatgpt"])}
        c = rows["claude"]
        self.assertEqual((c["positions"], c["open"], c["closed"]), (3, 1, 2))
        self.assertAlmostEqual(c["total_pnl"], 7.0)
        self.assertAlmostEqual(c["return_on_capital"], 7 / 300)
        self.assertAlmostEqual(c["avg_return"], 0.025)
        self.assertEqual((c["win_rate"], c["target_rate"], c["stop_rate"]), (0.5, 0.5, 0.5))
        self.assertEqual(c["booms"], 1)
        self.assertEqual(c["best"]["ticker"], "T1")
        self.assertEqual(c["worst"]["ticker"], "T2")
        self.assertEqual(c["equity"], [{"date": "2026-10-06", "pnl": 5.0}, {"date": "2026-10-07", "pnl": 7.0}])
        self.assertAlmostEqual(rows["grok"]["avg_alpha"], 0.03)
        self.assertEqual(rows["chatgpt"]["positions"], 0)
        self.assertEqual([r["model"] for r in board(self.trades, self.days, ["chatgpt", "grok", "claude"])],
                         ["claude", "grok", "chatgpt"])

    def test_bucket_and_window_filters(self):
        rows = {r["model"]: r for r in board(self.trades, self.days, ["claude", "grok"], bucket="moonshot")}
        self.assertEqual(rows["claude"]["positions"], 2)
        self.assertEqual(rows["grok"]["positions"], 0)
        rows = {r["model"]: r for r in board(self.trades, self.days, ["claude", "grok"], since=D2)}
        self.assertEqual(rows["claude"]["positions"], 1)
        self.assertEqual(rows["claude"]["total_pnl"], 2.0)

    def test_winners_and_summary(self):
        self.assertEqual(session_winners(self.days), {D1: "claude", D2: "grok"})
        s = session_summary(self.days, D2, ["claude", "grok"])
        self.assertEqual([r["model"] for r in s], ["grok", "claude"])
        self.assertEqual(s[1]["by_bucket"]["compounder"], 2.0)
        self.assertEqual(equity_curve({}), [])


if __name__ == "__main__":
    unittest.main()
