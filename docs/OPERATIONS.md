# Operations and troubleshooting

## Normal run

```bash
python -m unittest discover -s tests -t .
python -m arena.cli run
```

The scheduled workflow retries scoring several times after the close, on Sunday evening for Monday, and the following morning. The calendar is evaluated in America/New_York; UTC cron entries intentionally overlap daylight- and standard-time windows. Repeated runs are safe.

## Diagnosing missing Fruit Fly picks

1. Check the workflow log for the `fly:` result.
2. `no eligible reference prices` means all quote batches failed or produced ineligible data. No empty submission is stored; the next scheduled run retries.
3. Confirm the reference date is a completed session and inspect provider warnings.
4. Inspect `site/data/dashboard.json` health issues and `data/arena.db` submissions for the target session.
5. Run `PRICE_PROVIDER=fake python -m arena.cli demo --days 5` only against the isolated demo database; never copy demo output over production data.

## Provider failures

Missing prices are retried and are never stored as zero. yfinance remains the default free option. Polygon and Alpaca adapters are available when their environment variables are explicitly configured; no paid service is required or enabled automatically.

## Deployment

Merge and validate the application repository first. Then copy the versioned `site/index.html`, `site/app.js` and `site/app.css` release into `arinouri.ca/arena/`, update the cache-busting query string, test the raw data URL and merge the website repository separately. Do not create a second Pages deployment.

## Security

The workflow uses only `contents: write`. Provider credentials are read from environment variables and must never be printed. Raw submissions are untrusted text and are escaped by the dashboard before display.
