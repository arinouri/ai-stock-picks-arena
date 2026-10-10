import datetime as dt
import unittest

from arena import config
from arena.db import Benchmark, Position, PositionDay, Submission, connect
from arena.portfolio import simulate_model


class PortfolioTests(unittest.TestCase):
    def setUp(self):
        self.db = connect("sqlite://")()
        self.old_cost = config.COST_PER_SIDE
        config.COST_PER_SIDE = 0.001
        self.mon = dt.date(2026, 10, 5)
        self.tue = dt.date(2026, 10, 6)

    def tearDown(self):
        config.COST_PER_SIDE = self.old_cost
        self.db.close()

    def add_trade(self, ticker, rank, exit_price=110.0):
        sub = self.db.query(Submission).first()
        if sub is None:
            sub = Submission(model_key="claude", path="test", sha="test", run_date=self.mon,
                             ref_date=self.mon, target_date=self.tue, status="ok", raw="")
            self.db.add(sub)
        p = Position(model_key="claude", bucket="catalyst", rank=rank, ticker=ticker, horizon_days=1,
                     orig_target=110, orig_stop=90, target=110, stop=90, entry_date=self.mon,
                     first_session=self.tue, ref_price=100, entry_price=100, status="closed",
                     last_date=self.tue, last_price=exit_price, exit_date=self.tue, exit_price=exit_price,
                     exit_reason="time", sessions_held=1, benchmark_entry=100, benchmark_exit=101)
        p.days.append(PositionDay(date=self.tue, open=100, high=111, low=99, close=exit_price,
                                  mark=exit_price, prev_mark=100, event="time"))
        sub.positions.append(p)

    def test_fixed_capital_accounts_for_cash_costs_and_limits(self):
        for i in range(25):
            self.add_trade(f"T{i}", i)
        self.db.add(Benchmark(date=self.tue, open=100, close=101))
        self.db.commit()
        result = simulate_model(self.db.query(Position).all(), self.db.query(Benchmark).all(), "claude")
        metrics = result["metrics"]
        self.assertEqual(metrics["completed_trades"], config.PORTFOLIO_MAX_OPEN)
        self.assertEqual(metrics["skipped_for_capital"], 5)
        self.assertGreater(metrics["transaction_costs"], 0)
        self.assertGreater(metrics["total_return"], 0)
        self.assertAlmostEqual(metrics["benchmark_return"], 0.01)
        self.assertAlmostEqual(result["equity"][-1]["cash"], result["equity"][-1]["equity"])

    def test_unavailable_risk_metrics_are_null_not_zero(self):
        result = simulate_model([], [], "claude")
        self.assertIsNone(result["metrics"]["sharpe"])
        self.assertIsNone(result["metrics"]["annualized_return"])
        self.assertEqual(result["metrics"]["completed_trades"], 0)


if __name__ == "__main__":
    unittest.main()
