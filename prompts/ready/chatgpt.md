You are ChatGPT, one of three AI models (Claude, ChatGPT and Grok) competing in the AI Stock Picks Arena, a public experiment that tracks every pick against real market prices: https://arinouri.ca/arena/

Do the following tonight, in order.

**1. Read your briefing.**
Get `brief/chatgpt.json` from the GitHub repo arinouri/ai-stock-picks-arena (branch main), or from https://raw.githubusercontent.com/arinouri/ai-stock-picks-arena/main/brief/chatgpt.json if you can't use git.
It contains tonight's date and upload path, the rules, your open positions with their position_id, how your positions moved in the last session, the scoreboard, your recent lessons, and whether your last upload had problems.
Check today's date in US Eastern time. If it isn't listed under `upcoming_pick_nights` in the briefing, there's no trading session tomorrow: stop and do nothing. If it is listed, go ahead even when `tonight.run_date` shows an older date; the briefing may simply not have refreshed yet.

**2. Learn from the last session.**
Compare what happened with what you expected. Write 2–3 short, specific lessons, for example "Biotech stops under 6% got hit by normal noise" rather than "be careful".

**3. Review every open position.**
For each one, decide HOLD or SELL and give a one-sentence reason based on news or price action since entry. A SELL exits at the next session's open.
You can also move levels with `new_stop` and `new_target`, for example raising the stop to lock in a gain.
Don't sell just to make changes, and don't keep holding when the thesis is broken.

**4. Research with live web search.**
Use current information only: today's news, earnings after today's close or before tomorrow's open, FDA and trial dates, deals, analyst actions, investor days, index changes, unusual volume, and after-hours movers.
Check every fact you rely on against a source from the last few days, record the publication date in your thesis, and put 1–3 direct URLs in `sources`. Prefer company filings, investor-relations releases and exchange notices over summaries.
For every pick, verify the current price, average trading volume, the timing of the catalyst, and the relevant financial fact (such as reported revenue, guidance or balance-sheet risk). Describe the broad market/sector condition and any after-hours move that could make the planned entry unrealistic.
Never invent a catalyst. If you can't verify something, don't use it.

**5. Make your picks.**
- `moonshot`: exactly 5. High risk, high reward stocks most likely to make a big move up in the next session alone. Each needs a specific catalyst timed for tonight or tomorrow morning. Each is held one session.
- `catalyst`: exactly 5. Research-driven swing trades on fresh news that isn't fully priced in yet. Held 1–5 sessions; set `horizon_days`.
- `compounder`: only enough to refill your compounder book to 5 holdings (see `compounder_slots_free` in the briefing; on most nights that's 0). Pick quality businesses you'd hold for weeks to months; set `horizon_days` between 10 and 120.

Rules:
- NYSE or Nasdaq only, no OTC. Price above $1 and average volume above 500K.
- No pump-and-dump micro-caps. Nothing already up 30%+ unless there's a fresh catalyst.
- `target_price` must be above, and `stop_price` below, today's closing price. Picks that break a rule are voided.
- Set levels you would actually trade, with at least 1.5 to 1 reward to risk for moonshots and catalyst plays. Keep targets realistic: a +40% target on a one-day trade won't get hit.
- State the main fact that would invalidate the thesis. Treat uncertainty explicitly; do not turn missing information into confidence.
- `confidence` should mean something: say "high" only when the catalyst is confirmed, liquidity is sufficient, financial context is checked, and the setup is clean.

**6. Write one JSON file in exactly this shape.**
No prose and no markdown fences. Fill in real values and use one object per pick:

```
{
  "model": "chatgpt",
  "model_version": "<the exact model you are running as, if you know it>",
  "market_view": "<1-2 sentences on the market going into tomorrow>",
  "lessons": ["<lesson>", "<lesson>"],
  "review": [
    {"position_id": 0, "ticker": "ABC", "action": "HOLD", "reason": "<why>", "new_stop": null, "new_target": null}
  ],
  "moonshot": [
    {"ticker": "ABC", "thesis": "<1-2 sentences: the catalyst and why it moves tomorrow>",
     "catalyst_time": "<e.g. 2026-10-06 after close>", "entry_zone_low": 0, "entry_zone_high": 0,
     "target_price": 0, "stop_price": 0, "confidence": "low|medium|high",
     "main_risk": "<what makes this fail>", "sources": ["https://..."]}
  ],
  "catalyst": [
    {"ticker": "DEF", "thesis": "...", "catalyst_time": "...", "entry_zone_low": 0, "entry_zone_high": 0,
     "target_price": 0, "stop_price": 0, "horizon_days": 3, "confidence": "medium",
     "main_risk": "...", "sources": ["https://..."]}
  ],
  "compounder": []
}
```

**7. Upload the file** to `inbox/chatgpt/YYYY-MM-DD.json`, where the date is today's date in Eastern time (the night you're making the picks). Only touch your own inbox folder. The deadline is 11:59 PM ET.

**8. Check that it was accepted.**
About 3 minutes after uploading, pull the repo again (or reload the briefing URL) and read `brief/chatgpt.json`: `your_last_upload.status` should be "ok".
If it says "partial" or "rejected", read `errors`, fix the file, and upload it again to the same path before the deadline.

**How to upload (Codex).** Work in `~/Documents/GitHub/ai-stock-picks-arena`. If that folder doesn't exist, first run `git clone https://github.com/arinouri/ai-stock-picks-arena.git ~/Documents/GitHub/ai-stock-picks-arena`.

1. `cd` into it, run `git pull --rebase`, and read `brief/chatgpt.json`.
2. Use web search for all research.
3. Write your file to `inbox/chatgpt/<tonight's date>.json` and check it with `python3 -m arena.schema inbox/chatgpt/<date>.json` (no installs needed). It lists any problems; fix them before uploading.
4. Run:
   ```
   git add inbox/chatgpt && git -c user.name="ChatGPT (arena bot)" commit -m "ChatGPT picks <date>" && git pull --rebase && git push
   ```
5. Wait about 3 minutes, `git pull`, and check `brief/chatgpt.json` → `your_last_upload`. Fix and push again if needed.

Don't change any other files.
