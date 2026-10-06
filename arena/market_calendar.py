"""NYSE/Nasdaq trading calendar (full-day closures), rule-based so it never goes stale.

Early-close days (e.g. day after Thanksgiving) are treated as normal sessions: the
daily bar still exists, so scoring works the same.
"""
from __future__ import annotations

import datetime as dt
import os
from functools import lru_cache

# One-off closures not covered by the rules (national days of mourning etc.).
EXTRA_CLOSURES = {
    dt.date(2012, 10, 29),  # Hurricane Sandy
    dt.date(2012, 10, 30),
    dt.date(2018, 12, 5),  # President G.H.W. Bush
    dt.date(2025, 1, 9),  # President Carter
}


def _extra_from_env() -> set[dt.date]:
    """MARKET_EXTRA_HOLIDAYS=2027-01-02,2027-03-04 lets you add surprise closures."""
    out = set()
    for part in os.getenv("MARKET_EXTRA_HOLIDAYS", "").split(","):
        part = part.strip()
        if part:
            out.add(dt.date.fromisoformat(part))
    return out


def easter_sunday(year: int) -> dt.date:
    """Anonymous Gregorian algorithm."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return dt.date(year, month, day)


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> dt.date:
    d = dt.date(year, month, 1)
    offset = (weekday - d.weekday()) % 7
    return d + dt.timedelta(days=offset + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> dt.date:
    nxt = dt.date(year + (month == 12), month % 12 + 1, 1)
    d = nxt - dt.timedelta(days=1)
    return d - dt.timedelta(days=(d.weekday() - weekday) % 7)


def _observed(d: dt.date) -> dt.date:
    if d.weekday() == 5:  # Saturday -> Friday
        return d - dt.timedelta(days=1)
    if d.weekday() == 6:  # Sunday -> Monday
        return d + dt.timedelta(days=1)
    return d


@lru_cache(maxsize=64)
def holidays(year: int) -> frozenset[dt.date]:
    MON, THU = 0, 3
    h = set()
    # New Year's: Saturday is NOT moved to Friday Dec 31 (NYSE rule 7.2)
    ny = dt.date(year, 1, 1)
    if ny.weekday() == 6:
        h.add(ny + dt.timedelta(days=1))
    elif ny.weekday() != 5:
        h.add(ny)
    h.add(_nth_weekday(year, 1, MON, 3))  # MLK Day
    h.add(_nth_weekday(year, 2, MON, 3))  # Presidents' Day
    h.add(easter_sunday(year) - dt.timedelta(days=2))  # Good Friday
    h.add(_last_weekday(year, 5, MON))  # Memorial Day
    if year >= 2022:
        h.add(_observed(dt.date(year, 6, 19)))  # Juneteenth
    h.add(_observed(dt.date(year, 7, 4)))  # Independence Day
    h.add(_nth_weekday(year, 9, MON, 1))  # Labor Day
    h.add(_nth_weekday(year, 11, THU, 4))  # Thanksgiving
    h.add(_observed(dt.date(year, 12, 25)))  # Christmas
    return frozenset(h)


def is_trading_day(d: dt.date) -> bool:
    if d.weekday() >= 5:
        return False
    if d in holidays(d.year) or d in EXTRA_CLOSURES or d in _extra_from_env():
        return False
    return True


def next_trading_day(d: dt.date) -> dt.date:
    """First trading day strictly after d."""
    d = d + dt.timedelta(days=1)
    while not is_trading_day(d):
        d += dt.timedelta(days=1)
    return d


def previous_trading_day(d: dt.date) -> dt.date:
    """Last trading day strictly before d."""
    d = d - dt.timedelta(days=1)
    while not is_trading_day(d):
        d -= dt.timedelta(days=1)
    return d


def last_trading_day_on_or_before(d: dt.date) -> dt.date:
    return d if is_trading_day(d) else previous_trading_day(d)


def session_plan(run_date: dt.date) -> tuple[dt.date, dt.date]:
    """For picks made on the evening of run_date, return (ref_date, target_date).

    ref_date: the most recent session that has closed (its close = reference price).
    target_date: the next session the picks are for.
    Sunday evening -> ref = Friday, target = Monday.
    """
    return last_trading_day_on_or_before(run_date), next_trading_day(run_date)


def should_run_picks_tonight(run_date: dt.date) -> bool:
    """The 8:45 PM job runs only when *tomorrow* is a trading day.

    That gives Sun–Thu automatically and skips nights before holidays
    (e.g. the Thursday before Good Friday).
    """
    return is_trading_day(run_date + dt.timedelta(days=1))


def manual_run_date(now_et: dt.datetime) -> dt.date:
    """For a manual "Run picks now": before 9:30 AM ET on a trading day, pick for *today's*
    session (treat it as the night before); otherwise pick for the next session."""
    today = now_et.date()
    if is_trading_day(today) and now_et.time() < dt.time(9, 30):
        return today - dt.timedelta(days=1)
    return today
