# Arena methodology

AI Stock Picks Arena is a paper-trading research experiment. It does not place orders and its results are not investment returns.

## Timeline and fills

Picks are committed after a regular market close for the next NYSE/Nasdaq session. The reference close validates price, liquidity, stop and target rules. A valid position enters at the next available session open. The engine charges 0.10% on entry and 0.10% on exit.

Daily OHLC bars cannot establish intraday order. The engine therefore uses a conservative sequence: model sell at the open, stop, target, then time exit at the close. A gap through a stop or target fills at the open. If the same daily bar touches both levels, the stop wins. Missing data is never converted to a zero price; after five missing sessions an unentered position is void, while an entered position closes at its last valid mark with a `no_data` reason.

Prices are raw rather than dividend-adjusted so a historical adjusted OHLC series is not mistaken for an executable stop price. This means long-horizon total return can omit dividends. Splits, symbol changes, delistings and other corporate actions remain limitations of the free provider and must be reviewed when an outlier appears.

## Two different score views

The original research score assigns an independent $100 notional to every pick. It is useful for comparing trades and preserves the meaning of historical results, but it is not a funded portfolio.

The fixed-capital view gives each contestant $10,000, targets $500 per admitted position, and allows at most 20 open positions. Entry cost is included in the $500 cash debit. Exit proceeds, after exit cost, return to cash. Cash cannot be double-counted; same-day exits are conservatively unavailable to that morning's entries. Positions are admitted by session, submitted rank and stable database id. The view is reconstructed from stored fills and marks.

Reported portfolio analytics include total return, SPY-relative return, maximum drawdown, exposure, turnover, transaction costs, median trade return and profit factor. Annualized return requires at least one quarter of observations. Volatility, Sharpe and Sortino require at least 20 daily returns. An unavailable value is `null`, never a misleading zero.

## Learning agents

The Learner evaluates proposals from Claude, ChatGPT and Grok. Its features are recorded pick attributes. Training includes only AI positions whose exit date precedes the session being selected. Because it copies source picks, its observations are correlated with those contestants.

Fruit Fly is permanently uniform-random and is the scientific control.

Momentum is a non-learning baseline that ranks the same eligible universe by trailing 20-session return known at the reference close. It uses the same fixed exits as Fruit Fly and EVO. SPY buy-and-hold is the market benchmark.

Fruit Fly EVO is separate and independent. It selects from a liquid stock universe using only daily data through the reference close. Its version-1 features are an intercept, 5- and 20-session momentum, 20-session return relative to SPY, volatility, volume trend and drawdown. Features, model version, data version and deterministic exploration seed are stored with the decision. Completed EVO trades update a Bayesian linear contextual bandit in exit-date order.

EVO reward is:

`gross trade return - SPY return - 0.20 × maximum path drawdown - round-trip trading costs`

The result is clipped to ±0.50 so one outlier cannot dominate. The reward is a number, not an emotion. Cumulative reward is diagnostic and is not evidence of intelligence or profitability.

## Walk-forward evaluation

The exported evaluation uses an expanding window. Before each historical decision date, it trains only on positions whose exit date is earlier than that decision date. It then records the prediction without updating from that position's future outcome. A 20-observation warm-up is required. Mean absolute error, direction accuracy and prediction/outcome correlation are reported beside an explicitly labelled, optimistic in-sample fit. Only the forward result may be used to discuss generalization.

## Scientific limits

- The sample is small, strategies overlap, and trades are not independent.
- No profitability claim is valid without a sufficiently long forward-only evaluation.
- Yahoo Finance through `yfinance` is free and unofficial. Provider outages and revisions are possible.
- Daily bars approximate stops and targets; they do not model order-book liquidity.
- The cost estimate does not fully model spread, market impact or hard-to-borrow constraints.
- Sector analytics are not published until a point-in-time sector source can be stored without introducing present-day classification leakage.

Every raw AI upload, submission status, fill, mark, exit, model decision and generated CSV is retained for audit.
