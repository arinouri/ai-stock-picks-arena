# Architecture

The arena is a serverless batch pipeline built from Python, SQLite, GitHub Actions and a static dashboard.

1. Claude, ChatGPT and Grok write dated JSON to their own `inbox/` directory.
2. `arena.schema` parses the upload and `arena.engine` validates it against the last completed session.
3. Raw submissions and simulated positions are stored in `data/arena.db`; uploads remain the immutable source record.
4. `arena.engine.score` advances open positions through raw daily OHLC bars idempotently.
5. `arena.agents` runs the copied-pick Learner, the random Fruit Fly and independent Fruit Fly EVO.
6. `arena.portfolio` reconstructs equal-capital accounts without changing historical trade-level metrics.
7. `arena.export` writes static JSON, per-model audit files, briefings and CSV data under `site/data/`.
8. `site/` renders the public dashboard without a build step or application server.

`arinouri.ca/arena/` owns a same-origin copy of `index.html`, `app.js` and `app.css`. Its `index.html` points data reads at the raw `main/site/data/` path in this repository. Frontend releases therefore require a second reviewed change in `arinouri/arinouri.ca`; generated result updates remain in this repository only.

## Data compatibility

SQLite migrations are additive and run during `connect()`. Existing submissions and positions are never rewritten except for the original documented next-open migration. New EVO metadata lives in nullable `positions.selection_features` and `positions.agent_version`, so historical rows remain valid.

## Idempotency

Submission hashes prevent duplicate ingestion. A pre-deadline resubmission supersedes an earlier file for the same model/session. Scoring begins after the last stored mark. Agent submissions are keyed by target session and refuse to duplicate an active decision.
