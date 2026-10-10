import datetime as dt
import unittest

from arena.prices import Bar, PriceProvider, ResilientProvider


class ResilientProviderTests(unittest.TestCase):
    def test_retries_only_missing_symbols_and_rejects_bad_ohlc(self):
        day = dt.date(2026, 10, 5)

        class Partial(PriceProvider):
            name = "partial"

            def __init__(self):
                self.calls = []

            def daily_bars(self, tickers, start, end):
                self.calls.append(list(tickers))
                if len(self.calls) == 1:
                    return {"A": {day: Bar(10, 11, 9, 10, 1_000_000)},
                            "B": {day: Bar(10, 8, 9, 10, 1_000_000)}}  # impossible high
                return {"B": {day: Bar(20, 21, 19, 20, 2_000_000)}}

        inner = Partial()
        out = ResilientProvider(inner, attempts=2, delay=0).daily_bars(["A", "B"], day, day)
        self.assertEqual(set(out), {"A", "B"})
        self.assertEqual(inner.calls, [["A", "B"], ["B"]])


if __name__ == "__main__":
    unittest.main()
