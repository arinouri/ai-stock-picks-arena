"""Swappable price providers. Set PRICE_PROVIDER=yfinance|polygon|alpaca|fake.

All providers return *unadjusted-for-dividends* daily OHLC so the reference close and
the next session's bar are on the same basis.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import logging
import math
import os
import random
from dataclasses import dataclass
from typing import Optional
from zoneinfo import ZoneInfo

import requests


@dataclass(frozen=True)
class Bar:
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

from .market_calendar import is_trading_day, previous_trading_day

log = logging.getLogger(__name__)
NY = ZoneInfo("America/New_York")


class PriceProvider:
    name = "base"

    def daily_bars(self, tickers: list[str], start: dt.date, end: dt.date) -> dict[str, dict[dt.date, Bar]]:
        """Daily bars for each ticker, start..end inclusive."""
        raise NotImplementedError

    def intraday(self, ticker: str, day: dt.date) -> list[list]:
        """[[iso_time, price], ...] for one session; empty list if unavailable."""
        return []

    # Convenience helpers built on daily_bars --------------------------------
    def bars_on(self, tickers: list[str], day: dt.date) -> dict[str, Optional[Bar]]:
        data = self.daily_bars(tickers, day, day)
        return {t: data.get(t, {}).get(day) for t in tickers}

    def history(self, tickers: list[str], end: dt.date, calendar_days: int = 40) -> dict[str, dict[dt.date, Bar]]:
        return self.daily_bars(tickers, end - dt.timedelta(days=calendar_days), end)


# --------------------------------------------------------------------------- yfinance


class YFinanceProvider(PriceProvider):
    name = "yfinance"

    def daily_bars(self, tickers, start, end):
        import yfinance as yf  # imported lazily so tests don't need it

        tickers = sorted(set(tickers))
        if not tickers:
            return {}
        df = yf.download(
            [t.replace(".", "-") for t in tickers],
            start=start.isoformat(),
            end=(end + dt.timedelta(days=1)).isoformat(),
            interval="1d",
            auto_adjust=False,
            group_by="ticker",
            progress=False,
            threads=True,
        )
        out: dict[str, dict[dt.date, Bar]] = {}
        if df is None or df.empty:
            return out
        for t in tickers:
            yt = t.replace(".", "-")
            try:
                sub = df[yt] if len(tickers) > 1 or yt in df.columns.get_level_values(0) else df
            except KeyError:
                continue
            bars = {}
            for idx, row in sub.iterrows():
                o, h, l, c = row.get("Open"), row.get("High"), row.get("Low"), row.get("Close")
                if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in (o, h, l, c)):
                    continue
                vol = row.get("Volume", 0) or 0
                bars[idx.date()] = Bar(float(o), float(h), float(l), float(c), float(vol))
            if bars:
                out[t] = bars
        return out

    def intraday(self, ticker, day):
        import yfinance as yf

        try:
            df = yf.Ticker(ticker.replace(".", "-")).history(
                start=day.isoformat(), end=(day + dt.timedelta(days=1)).isoformat(), interval="5m"
            )
        except Exception as e:  # pragma: no cover - network
            log.warning("intraday %s failed: %s", ticker, e)
            return []
        return [[ts.isoformat(), round(float(r["Close"]), 4)] for ts, r in df.iterrows() if r["Close"] == r["Close"]]


# --------------------------------------------------------------------------- Polygon


class PolygonProvider(PriceProvider):
    name = "polygon"

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("POLYGON_API_KEY is required for PRICE_PROVIDER=polygon")
        self.api_key = api_key
        self.base = os.getenv("POLYGON_BASE_URL", "https://api.polygon.io")

    def _aggs(self, ticker, mult, span, start, end):
        url = f"{self.base}/v2/aggs/ticker/{ticker}/range/{mult}/{span}/{start}/{end}"
        r = requests.get(url, params={"adjusted": "false", "sort": "asc", "limit": 50000, "apiKey": self.api_key}, timeout=30)
        r.raise_for_status()
        return r.json().get("results", []) or []

    def daily_bars(self, tickers, start, end):
        out = {}
        for t in sorted(set(tickers)):
            try:
                rows = self._aggs(t, 1, "day", start.isoformat(), end.isoformat())
            except Exception as e:
                log.warning("polygon %s failed: %s", t, e)
                continue
            bars = {}
            for r in rows:
                d = dt.datetime.fromtimestamp(r["t"] / 1000, tz=NY).date()
                bars[d] = Bar(r["o"], r["h"], r["l"], r["c"], r.get("v", 0))
            if bars:
                out[t] = bars
        return out

    def intraday(self, ticker, day):
        try:
            rows = self._aggs(ticker, 5, "minute", day.isoformat(), day.isoformat())
        except Exception:
            return []
        pts = []
        for r in rows:
            ts = dt.datetime.fromtimestamp(r["t"] / 1000, tz=NY)
            if dt.time(9, 30) <= ts.time() <= dt.time(16, 0):
                pts.append([ts.isoformat(), r["c"]])
        return pts


# --------------------------------------------------------------------------- Alpaca


class AlpacaProvider(PriceProvider):
    name = "alpaca"
    base = "https://data.alpaca.markets/v2/stocks/bars"

    def __init__(self, key_id: str, secret: str):
        if not (key_id and secret):
            raise ValueError("ALPACA_API_KEY_ID and ALPACA_API_SECRET are required for PRICE_PROVIDER=alpaca")
        self.headers = {"APCA-API-KEY-ID": key_id, "APCA-API-SECRET-KEY": secret}
        self.feed = os.getenv("ALPACA_FEED", "iex")  # free plan = iex (volume is IEX-only)

    def _bars(self, tickers, timeframe, start_iso, end_iso):
        params = {"symbols": ",".join(tickers), "timeframe": timeframe, "start": start_iso, "end": end_iso,
                  "adjustment": "raw", "feed": self.feed, "limit": 10000}
        out: dict[str, list] = {}
        while True:
            r = requests.get(self.base, headers=self.headers, params=params, timeout=30)
            r.raise_for_status()
            js = r.json()
            for sym, rows in (js.get("bars") or {}).items():
                out.setdefault(sym, []).extend(rows)
            tok = js.get("next_page_token")
            if not tok:
                return out
            params["page_token"] = tok

    def daily_bars(self, tickers, start, end):
        if not tickers:
            return {}
        raw = self._bars(sorted(set(tickers)), "1Day", start.isoformat(), (end + dt.timedelta(days=1)).isoformat())
        out = {}
        for sym, rows in raw.items():
            bars = {}
            for r in rows:
                d = dt.datetime.fromisoformat(r["t"].replace("Z", "+00:00")).astimezone(NY).date()
                if start <= d <= end:
                    bars[d] = Bar(r["o"], r["h"], r["l"], r["c"], r.get("v", 0))
            out[sym] = bars
        return out

    def intraday(self, ticker, day):
        s = dt.datetime.combine(day, dt.time(9, 30), NY).isoformat()
        e = dt.datetime.combine(day, dt.time(16, 0), NY).isoformat()
        try:
            rows = self._bars([ticker], "5Min", s, e).get(ticker, [])
        except Exception:
            return []
        return [[dt.datetime.fromisoformat(r["t"].replace("Z", "+00:00")).astimezone(NY).isoformat(), r["c"]] for r in rows]


# --------------------------------------------------------------------------- Fake (demo/tests)


class FakeProvider(PriceProvider):
    """Deterministic synthetic prices: same ticker+date always gives the same bar."""

    name = "fake"

    ANCHOR = dt.date(2026, 1, 2)

    def __init__(self, overrides: Optional[dict] = None, missing: Optional[set] = None):
        self.overrides = overrides if overrides is not None else {}  # {(ticker, date): Bar}
        self.missing = missing or set()  # tickers that return no data
        self._closes: dict[tuple[str, dt.date], float] = {}

    @staticmethod
    def _seed(*parts) -> int:
        return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:12], 16)

    def _ret(self, ticker: str, day: dt.date) -> float:
        rng = random.Random(self._seed(ticker, day, "ret"))
        r = rng.gauss(-0.005, 0.04)
        if rng.random() < 0.05:  # occasional "boom"
            r += rng.uniform(0.08, 0.30)
        return max(r, -0.6)

    def _close(self, ticker: str, day: dt.date) -> float:
        """Exact close: compounding walk from ANCHOR, cached, so close(d) feeds bar(d+1)."""
        key = (ticker, day)
        if key in self._closes:
            return self._closes[key]
        days, d = [], day
        while d > self.ANCHOR and (ticker, d) not in self._closes:
            days.append(d)
            d = previous_trading_day(d)
        value = self._closes.get((ticker, d), 5 + (self._seed(ticker) % 29500) / 100)  # $5–$300 start
        for d in reversed(days):
            value = value * (1 + self._ret(ticker, d))
            self._closes[(ticker, d)] = value
        self._closes.setdefault(key, value)
        return self._closes[key]

    def _bar(self, ticker: str, day: dt.date) -> Bar:
        if (ticker, day) in self.overrides:
            return self.overrides[(ticker, day)]
        prev = self._close(ticker, previous_trading_day(day))
        r = self._ret(ticker, day)
        rng = random.Random(self._seed(ticker, day))
        o = prev * (1 + rng.gauss(0, 0.012) + r * 0.3)
        c = self._close(ticker, day)
        h = max(o, c) * (1 + abs(rng.gauss(0, 0.02)))
        l = min(o, c) * (1 - abs(rng.gauss(0, 0.02)))
        return Bar(round(o, 2), round(h, 2), round(l, 2), round(c, 2), rng.uniform(6e5, 3e7))

    def daily_bars(self, tickers, start, end):
        out = {}
        for t in tickers:
            if t in self.missing:
                continue
            bars = {}
            d = start
            while d <= end:
                if is_trading_day(d):
                    bars[d] = self._bar(t, d)
                d += dt.timedelta(days=1)
            out[t] = bars
        return out

    def intraday(self, ticker, day):
        if ticker in self.missing:
            return []
        b = self._bar(ticker, day)
        rng = random.Random(self._seed(ticker, day, "intraday"))
        n = 78  # 5-minute bars 9:30–16:00
        hi_i, lo_i = sorted(rng.sample(range(1, n - 1), 2))
        if rng.random() < 0.5:
            hi_i, lo_i = lo_i, hi_i
        anchors = {0: b.open, hi_i: b.high, lo_i: b.low, n - 1: b.close}
        keys = sorted(anchors)
        pts = []
        start = dt.datetime.combine(day, dt.time(9, 30), NY)
        for i in range(n):
            k0 = max(k for k in keys if k <= i)
            k1 = min(k for k in keys if k >= i)
            v = anchors[k0] if k0 == k1 else anchors[k0] + (anchors[k1] - anchors[k0]) * (i - k0) / (k1 - k0)
            if i not in anchors:
                v *= 1 + rng.gauss(0, 0.002)
                v = min(max(v, b.low), b.high)
            pts.append([(start + dt.timedelta(minutes=5 * i)).isoformat(), round(v, 2)])
        return pts


def get_provider(name: Optional[str] = None) -> PriceProvider:
    from . import config

    name = (name or config.PRICE_PROVIDER).lower()
    if name == "yfinance":
        return YFinanceProvider()
    if name == "polygon":
        return PolygonProvider(config.POLYGON_API_KEY)
    if name == "alpaca":
        return AlpacaProvider(config.ALPACA_API_KEY_ID, config.ALPACA_API_SECRET)
    if name == "fake":
        return FakeProvider()
    raise ValueError(f"Unknown PRICE_PROVIDER {name!r} (use yfinance, polygon, alpaca or fake)")
