import datetime as dt
import unittest

from arena.market_calendar import (
    easter_sunday,
    holidays,
    is_trading_day,
    next_trading_day,
    session_plan,
    manual_run_date,
    should_run_picks_tonight,
)

d = dt.date


class CalendarTests(unittest.TestCase):
    def test_easter(self):
        self.assertEqual(easter_sunday(2026), d(2026, 4, 5))
        self.assertEqual(easter_sunday(2027), d(2027, 3, 28))
        self.assertEqual(easter_sunday(2024), d(2024, 3, 31))

    def test_2026_holidays(self):
        expected = {
            d(2026, 1, 1), d(2026, 1, 19), d(2026, 2, 16), d(2026, 4, 3), d(2026, 5, 25),
            d(2026, 6, 19), d(2026, 7, 3), d(2026, 9, 7), d(2026, 11, 26), d(2026, 12, 25),
        }
        self.assertEqual(set(holidays(2026)), expected)

    def test_2027_observed_rules(self):
        h = holidays(2027)
        self.assertIn(d(2027, 6, 18), h)  # Juneteenth Sat -> Fri
        self.assertIn(d(2027, 7, 5), h)  # July 4 Sun -> Mon
        self.assertIn(d(2027, 12, 24), h)  # Christmas Sat -> Fri
        self.assertNotIn(d(2027, 12, 31), h)

    def test_new_year_on_saturday_not_observed(self):
        # Jan 1 2022 was a Saturday: NYSE stayed open Fri Dec 31 2021
        self.assertTrue(is_trading_day(d(2021, 12, 31)))

    def test_weekend_and_special(self):
        self.assertFalse(is_trading_day(d(2026, 10, 10)))  # Saturday
        self.assertFalse(is_trading_day(d(2025, 1, 9)))  # Carter day of mourning
        self.assertTrue(is_trading_day(d(2026, 10, 6)))

    def test_next_trading_day(self):
        self.assertEqual(next_trading_day(d(2026, 10, 9)), d(2026, 10, 12))  # Fri -> Mon
        self.assertEqual(next_trading_day(d(2026, 4, 2)), d(2026, 4, 6))  # skips Good Friday

    def test_session_plan(self):
        self.assertEqual(session_plan(d(2026, 10, 6)), (d(2026, 10, 6), d(2026, 10, 7)))  # Tue
        self.assertEqual(session_plan(d(2026, 10, 11)), (d(2026, 10, 9), d(2026, 10, 12)))  # Sun
        self.assertEqual(session_plan(d(2026, 11, 26)), (d(2026, 11, 25), d(2026, 11, 27)))  # Thanksgiving

    def test_should_run_tonight(self):
        week = {d(2026, 10, 4 + i): should_run_picks_tonight(d(2026, 10, 4 + i)) for i in range(7)}
        # Sun..Thu True, Fri/Sat False
        self.assertEqual(list(week.values()), [True, True, True, True, True, False, False])
        self.assertFalse(should_run_picks_tonight(d(2026, 4, 2)))  # Thu before Good Friday
        self.assertFalse(should_run_picks_tonight(d(2026, 11, 25)))  # Wed before Thanksgiving
        self.assertTrue(should_run_picks_tonight(d(2026, 11, 26)))  # Thanksgiving night -> Fri session

    def test_manual_run_date(self):
        mk = lambda day, h: dt.datetime.combine(day, dt.time(h, 0))
        self.assertEqual(manual_run_date(mk(d(2026, 10, 6), 1)), d(2026, 10, 5))  # 1 AM Tue -> Tue session
        self.assertEqual(manual_run_date(mk(d(2026, 10, 6), 12)), d(2026, 10, 6))  # noon Tue -> Wed session
        self.assertEqual(manual_run_date(mk(d(2026, 10, 10), 1)), d(2026, 10, 10))  # Saturday -> Monday


if __name__ == "__main__":
    unittest.main()
