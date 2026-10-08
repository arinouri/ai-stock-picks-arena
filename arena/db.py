"""SQLite schema. The database file (data/arena.db) is committed to the repo by the GitHub Action,
and every raw submission stays in inbox/, so the whole history is auditable."""
from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from . import config


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class AIModel(Base):
    __tablename__ = "models"
    key: Mapped[str] = mapped_column(String(32), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(64))
    maker: Mapped[str] = mapped_column(String(64), default="")
    color: Mapped[str] = mapped_column(String(16), default="#888888")


class Submission(Base):
    """One file a bot dropped into inbox/<model>/<run_date>.json."""

    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_key: Mapped[str] = mapped_column(ForeignKey("models.key"), index=True)
    path: Mapped[str] = mapped_column(String(256))
    sha: Mapped[str] = mapped_column(String(64), index=True)
    run_date: Mapped[dt.date] = mapped_column(Date)  # the evening the picks were made (ET)
    ref_date: Mapped[dt.date] = mapped_column(Date)  # session whose close is the entry price
    target_date: Mapped[dt.date] = mapped_column(Date, index=True)  # first session the picks trade
    received_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)  # UTC, when the Action saw it
    status: Mapped[str] = mapped_column(String(16), default="ok")  # ok | partial | rejected | late | superseded
    errors: Mapped[list] = mapped_column(JSON, default=list)
    market_view: Mapped[str] = mapped_column(Text, default="")
    lessons: Mapped[list] = mapped_column(JSON, default=list)
    model_version: Mapped[str] = mapped_column(String(128), default="")
    author: Mapped[str] = mapped_column(String(128), default="")  # git commit author, for auditing
    raw: Mapped[str] = mapped_column(Text, default="")

    model: Mapped[AIModel] = relationship()
    positions: Mapped[list["Position"]] = relationship(back_populates="submission")
    reviews: Mapped[list["Review"]] = relationship(back_populates="submission", cascade="all, delete-orphan")


class Position(Base):
    """A simulated $100 buy at the next session's open, held until stop, target, time limit or the model sells."""

    __tablename__ = "positions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_key: Mapped[str] = mapped_column(ForeignKey("models.key"), index=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"))
    bucket: Mapped[str] = mapped_column(String(16), index=True)
    rank: Mapped[int] = mapped_column(Integer, default=0)
    ticker: Mapped[str] = mapped_column(String(12), index=True)
    thesis: Mapped[str] = mapped_column(Text, default="")
    catalyst_time: Mapped[str] = mapped_column(String(80), default="")
    sources: Mapped[list] = mapped_column(JSON, default=list)
    entry_zone_low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    entry_zone_high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence: Mapped[str] = mapped_column(String(8), default="medium")
    main_risk: Mapped[str] = mapped_column(Text, default="")
    horizon_days: Mapped[int] = mapped_column(Integer, default=1)
    orig_target: Mapped[float] = mapped_column(Float)
    orig_stop: Mapped[float] = mapped_column(Float)
    target: Mapped[float] = mapped_column(Float)  # current (models can move them in nightly reviews)
    stop: Mapped[float] = mapped_column(Float)

    entry_date: Mapped[dt.date] = mapped_column(Date)  # = submission.ref_date
    first_session: Mapped[dt.date] = mapped_column(Date, index=True)  # = submission.target_date
    ref_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # close when picked (rules check)
    entry_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # open of first_session
    benchmark_entry: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    flags: Mapped[list] = mapped_column(JSON, default=list)
    source_position_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Learner copies

    status: Mapped[str] = mapped_column(String(12), default="open", index=True)  # open | closed | void
    sell_at_open_on: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    last_date: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    last_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sessions_held: Mapped[int] = mapped_column(Integer, default=0)
    missing_sessions: Mapped[int] = mapped_column(Integer, default=0)
    exit_date: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    exit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    exit_reason: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)  # target|stop|time|model_sell|void
    benchmark_exit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # First-session stats (the original "did it explode tomorrow?" contest)
    d1_open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    d1_high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    d1_low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    d1_close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    d1_intraday: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    submission: Mapped[Submission] = relationship(back_populates="positions")
    days: Mapped[list["PositionDay"]] = relationship(
        back_populates="position", cascade="all, delete-orphan", order_by="PositionDay.date"
    )

    # ---- derived values
    def gross_ret(self) -> Optional[float]:
        price = self.exit_price if self.status == "closed" else self.last_price
        if price is None or not self.entry_price:
            return None
        return price / self.entry_price - 1

    def ret(self) -> Optional[float]:
        """Return after trading costs (in and out; open positions are valued as if sold now)."""
        g = self.gross_ret()
        return None if g is None else g - 2 * config.COST_PER_SIDE

    def pnl(self) -> float:
        r = self.ret()
        return 0.0 if r is None else r * config.NOTIONAL

    def benchmark_ret(self, latest_benchmark: Optional[float] = None) -> Optional[float]:
        end = self.benchmark_exit if self.status == "closed" else latest_benchmark
        if not self.benchmark_entry or end is None:
            return None
        return end / self.benchmark_entry - 1

    def d1(self) -> dict:
        if self.d1_close is None or not self.entry_price:
            return {}
        e = self.entry_price
        return {
            "pct_to_open": self.d1_open / e - 1,
            "pct_to_close": self.d1_close / e - 1,
            "pct_to_high": self.d1_high / e - 1,
            "pct_to_low": self.d1_low / e - 1,
            "hit_target": self.d1_high >= self.orig_target and not self.d1_low <= self.orig_stop,
            "hit_stop": self.d1_low <= self.orig_stop,
            "boom": self.d1_high / e - 1 >= config.BOOM_THRESHOLD - 1e-12,
        }


class PositionDay(Base):
    __tablename__ = "position_days"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"), index=True)
    date: Mapped[dt.date] = mapped_column(Date, index=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    mark: Mapped[float] = mapped_column(Float)  # close, or the exit price on the exit day
    prev_mark: Mapped[float] = mapped_column(Float)  # previous mark (entry price on day 1)
    event: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    position: Mapped[Position] = relationship(back_populates="days")

    @property
    def pnl(self) -> float:
        """Dollar P&L of the $100 position on this session (trading costs are charged on the first one)."""
        cost = 2 * config.COST_PER_SIDE * config.NOTIONAL if self.date == self.position.first_session else 0.0
        return config.NOTIONAL * (self.mark - self.prev_mark) / self.position.entry_price - cost


class Review(Base):
    """A model's nightly call on one of its open positions."""

    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), index=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"), index=True)
    action: Mapped[str] = mapped_column(String(8))  # HOLD | SELL
    reason: Mapped[str] = mapped_column(Text, default="")
    new_stop: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    new_target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    effective_date: Mapped[dt.date] = mapped_column(Date)

    submission: Mapped[Submission] = relationship(back_populates="reviews")
    position: Mapped[Position] = relationship()


class Benchmark(Base):
    __tablename__ = "benchmark"
    date: Mapped[dt.date] = mapped_column(Date, primary_key=True)
    close: Mapped[float] = mapped_column(Float)
    open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


def _migrate(engine) -> None:
    """Add columns introduced after the database was first created (SQLite has no auto-migrate)."""
    from sqlalchemy import inspect, text

    added = {"positions": {"source_position_id": "INTEGER", "ref_price": "FLOAT"}, "benchmark": {"open": "FLOAT"}}
    insp = inspect(engine)
    with engine.begin() as conn:
        for table, cols in added.items():
            have = {c["name"] for c in insp.get_columns(table)}
            for name, sqltype in cols.items():
                if name not in have:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {sqltype}"))
                    if (table, name) == ("positions", "ref_price"):
                        # Switch from "bought at the close" to "bought at the next open": positions that
                        # haven't traded yet keep the close as their reference and get their entry at the open.
                        conn.execute(text("UPDATE positions SET ref_price = entry_price"))
                        conn.execute(text("UPDATE positions SET entry_price = NULL, last_price = NULL, "
                                          "benchmark_entry = NULL WHERE status = 'open' AND sessions_held = 0"))


def connect(url: Optional[str] = None) -> sessionmaker:
    url = url or config.DATABASE_URL
    kwargs = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {}
    engine = create_engine(url, future=True, **kwargs)
    Base.metadata.create_all(engine)
    _migrate(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    with Session() as s:
        for key, m in config.MODELS.items():
            row = s.get(AIModel, key)
            if row is None:
                s.add(AIModel(key=key, **m))
            else:
                row.display_name, row.maker, row.color = m["display_name"], m["maker"], m["color"]
        s.commit()
    return Session
