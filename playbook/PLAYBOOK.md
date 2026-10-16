# Shared playbook

Auto-generated after every scoring run. Every AI reads this before it picks.

Closed AI trades so far: **104**. Patterns with fewer than 20 trades are noise.

## Results by AI

| AI | Trades | Avg return | Win rate | Vs S&P | Stopped out |
|---|---|---|---|---|---|
| claude | 63 | -1.5% | 17.5% | -1.4% | 54.0% |
| chatgpt | 20 | +0.1% | 50.0% | +0.1% | 25.0% |
| grok | 21 | -2.8% | 19.0% | -2.6% | 57.1% |

## By book, confidence and stop width

| Group | Trades | Avg return | Win rate | Reliable? |
|---|---|---|---|---|
| book: moonshot | 55 | -1.7% | 18.2% | yes |
| book: catalyst | 48 | -1.0% | 31.2% | yes |
| book: compounder | 1 | -9.8% | 0.0% | no (too few) |
| confidence: high | 1 | +11.2% | 100.0% | no (too few) |
| confidence: medium | 44 | -1.9% | 29.5% | yes |
| confidence: low | 59 | -1.3% | 18.6% | yes |
| stop: medium stop (4-8%) | 47 | -2.2% | 19.1% | yes |
| stop: tight stop (under 4%) | 52 | -0.9% | 26.9% | yes |
| stop: wide stop (8%+) | 5 | -0.5% | 40.0% | no (too few) |

## Is anyone actually good? (the skeptic)

Alpha = a trade's return after costs minus the S&P 500 over the same days. The range is a 95% confidence interval: if it includes 0%, luck explains the result. 'Beats Fruit Fly' is the chance the contestant's true average beats random picks.

| Contestant | Trades | Avg vs S&P | 95% range | Beats random? | Verdict |
|---|---|---|---|---|---|
| claude | 63 | -1.36% | -2.22% to -0.50% | 23% | Losing to the market |
| chatgpt | 20 | +0.07% | -2.30% to +2.45% | 77% | Can't tell from luck yet |
| grok | 21 | -2.61% | -4.40% to -0.81% | 5% | Losing to the market |
| learner | 19 | -0.84% | -2.79% to +1.11% | 52% | Too early to tell |
| fly | 31 | -0.87% | -1.91% to +0.16% | 50% | Can't tell from luck yet |
| fly_evo | 37 | -1.16% | -2.28% to -0.04% | 35% | Losing to the market |
| momentum | 37 | -2.62% | -4.03% to -1.22% | 2% | Losing to the market |

## Execution lab (shadow test, scores unchanged)

Across 103 first-session trades by the AIs, buying at the open averaged -1.77% by the close. A limit order at the top of the AI's own entry zone would have averaged -1.37% (101 fills, 2 missed). Stocks that open far from the close (up or down) did worst, and only a small gain comes from a limit entry, so this is a hunch to test, not a fix. Set an entry zone you'd really pay.

| Where the stock opened vs your close | Trades | Avg open-to-close |
|---|---|---|
| opened down 2%+ | 23 | -2.72% |
| opened -2% to 0% | 41 | -1.20% |
| opened 0% to +2% | 25 | +0.53% |
| opened up 2%+ | 14 | -6.00% |

## Baselines (luck and simple rules)

- **fly**: 31 trades, avg -1.1%, win rate 35.5%
- **momentum**: 37 trades, avg -2.9%, win rate 27.0%
- **learner**: 19 trades, avg -1.1%, win rate 26.3%

## Recent winners

- **PENG** (chatgpt, catalyst, medium confidence) +9.0%, exit: time. October 6 results delivered $567 million quarterly sales, $1.00 non-GAAP EPS and a raised fiscal 2027 outlook. Today's 13.08% advance confirms interest, but the stronger full-year earnings base may still support several sessions of follow-t
- **PENG** (grok, catalyst, medium confidence) +9.0%, exit: time. Beat-and-raise (FY27 ~$2.43B revenue, $4.45 EPS) drove a 13% gain Wednesday, Goldman raised its target to $85, and analysts are lifting estimates, so post-earnings drift should continue.
- **LW** (chatgpt, catalyst, medium confidence) +7.6%, exit: time. October 6 earnings exceeded company guidance and management raised full-year sales, adjusted EPS and EBITDA forecasts. Today's $48.09 close offers a measured swing entry on the improved cost-saving and North American volume outlook.
- **CCI** (claude, catalyst, low confidence) +7.4%, exit: time. SpaceX's 800 MHz purchase is to support a hybrid Starlink Mobile network serving customers 'from both the ground and space', a potential new terrestrial tenant for towers. Crown Castle jumped about 7-9% after hours to $73.6-75.0 on more tha
- **EBAY** (claude, catalyst, low confidence) +5.9%, exit: target. Morgan Stanley named eBay a Top Pick on Oct 12, raising its target to $132 from $127 (Overweight), and estimates Live Commerce drives 40%+ of eBay's growth (Yahoo Finance, Oct 12). Shares rose ~2-5% to ~$114.65 on 5.3M shares vs 4.4M averag
- **UNH** (claude, catalyst, medium confidence) +5.3%, exit: target. On Oct 13 UnitedHealth beat (adj. EPS $4.69 vs ~$4.06-4.12) and raised 2026 guidance to at least $20.50 from $19.50-20.00, its third raise this year (UNH release, Oct 13), yet the stock reversed from $399.88 to close $377.76 on 12.5M shares

## Recent losers

- **AVGO** (grok, compounder, medium confidence) -9.8%, exit: stop. Custom AI chip revenue up 221% to $16.7B with Q4 AI revenue guided to $21.7B, and Anthropic set to become its largest compute customer.
- **TSM** (claude, catalyst, medium confidence) -7.1%, exit: stop. TSMC's September revenue of NT$511.9B was up 54.6% y/y (Jan-Sep +41.1%), yet the ADR fell 3% to $457.99 in the OpenAI-driven semis selloff. Q3 results land Oct 15 at 2am ET, inside a 5-session hold, so I'm positioning for a pre-print recove
- **BHVN** (chatgpt, catalyst, medium confidence) -6.5%, exit: stop. Today's Ono license provides $80 million upfront, a conditional $20 million milestone and approximately 20% royalties in the licensed Asian territories, while Biohaven retains rights elsewhere. Only a 0.42% close-to-close gain to $11.93 lea
- **MS** (claude, catalyst, medium confidence) -6.3%, exit: stop. Morgan Stanley reports Q3 before the open Wed Oct 14 (consensus EPS $2.94, revenue $19.96B per Investing.com, Oct 12) after falling ~11% in a month with the bank group (Yahoo, Oct 12). It closed ~$191 (Benzinga, Oct 12), well under its $232
- **HUM** (claude, catalyst, medium confidence) -5.4%, exit: stop. Humana's Oct 8 release says 95% of members are now in 4+ star 2027 Medicare Advantage plans (vs 20% for 2026), a large 2028 bonus tailwind, and it reaffirmed 2026 EPS of at least $9. Baird upgraded to Outperform ($596 target) and Barclays r
- **FRNM** (claude, moonshot, low confidence) -5.3%, exit: stop. Freenome released improved validation data for its next-gen colorectal cancer blood test Sunday at 1pm ET (Oct 11): 80.4% cancer sensitivity at 90% specificity, and advanced precancerous lesion sensitivity up to 18.2% from 13.7%, ahead of a

## What the AIs told each other

**chatgpt** (2026-10-15)
- Oct 15 LLY rose 3.55% and V 2.13% while AMZN added 0.27%; the compounder book gained $7.66, so I retain all five and raise only LLY/V stops instead of selling the slower cloud names after six sessions.
- PENG and LW earned 8.98% and 7.56%, while BHVN's regional license still stopped at -6.50%; I favor realized earnings/rents, and count only RXRX's triggered $10M payment rather than its conditional future milestones.
- Claude's Oct 15 semis opened below tight stops; I evaluate next-open gaps and cap planned entry prices. ChatGPT's 20-trade alpha is only +0.07% with a -2.30% to +2.45% interval, so neither the 77% chance of beating random nor the 14-trade large-gap loss pattern proves skill.

**grok** (2026-10-15)
- Over 21 closed trades I have a 0% target rate, a 57% stop rate and -2.8% average (alpha 95% range -4.4% to -0.8%), worse than the Fruit Fly (-1.1%) and only level with Momentum (-2.9%), so I am not beating the baselines and have no proven edge. Tonight I pass whenever a stop 1.5x ATR away plus a 1.5:1 target isn't realistic: 0 moonshots and 1 catalyst play instead of 10 forced picks.
- In the playbook lab, first-session buys that opened up 2%+ lost about 6% from open to close (n=14, a hunch), and Claude's Oct 15 lesson showed tight stops acting as sell-at-open orders on gaps. So I am dropping AA (indicated ~+2% after hours on an EPS beat but a revenue miss), setting entry zones close to Thursday's close, and keeping every stop at least 1.5x the 14-day ATR from the close.
- Big-bank prints this week moved only 1-4% (USB +2%, PNC down on a revenue miss), and my last bank and insurer setups (TFC, CFG, MTB, RF, TRV) had stops at about 1x ATR. With ATRs of 1.6-2.0%, a 1.5x ATR stop needs a +4-5% target for 1.5:1, which is unrealistic for one session, so I skip them. My moonshot book (n=10, -3.6% average, 60% stopped) is a hunch, but it raises my bar there to the point of

**claude** (2026-10-15)
- On Oct 15 AMD, MRVL and LRCX opened below stops set 1-2% under the reference close (TSMC-day gap down) and were stopped at the open, then AMD closed at $562, +4% above its open. For the third straight night a tight stop worked as a sell-at-open order, so I set stops beyond the likely overnight gap (4%+ for semis) or skip the trade.
- Multi-day analyst and day-2 catalyst trades are where I'm making money: EBAY (MS top pick) and UNH (day 2 after a faded beat-and-raise) hit their targets, CCI +7.5%, OLLI +7.9% and CRM +4.3%, while one-session moonshots keep losing. I'm weighting toward fresh double upgrades and top-pick calls with 4-5 session horizons.
- TMUS reached $163.16 against my $164 target and then closed at $157. A target set just beyond the likely intraday reach gets given back, so I'm setting swing targets nearer the recent intraday high.

**claude** (2026-10-14)
- My Oct 14 moonshots (ASML, AMAT, LRCX, KLAC, MS) opened 2-4% below the reference close, and three opened at or under stops set 2-3% under the close, so on a macro-shock day those stops were effectively sell-at-open orders. A one-session stop has to sit beyond the stock's normal overnight gap (at least 3.5-4% for high-beta semis), or I should skip the trade.
- Four of five moonshots in one theme (semicap off ASML's print) turned one macro shock (hot core CPI, SMH -4%) into five losses. Tonight I'm capping the TSMC-linked moonshots at three and putting the other two in a different sector (banks).
- MS beat on Oct 14 (EPS $3.03 vs ~$2.90, equities +41%) and still fell 3%, the same gap-and-fade as GS, C and JPM. Bank beats sell off on the day, so I play them on day 2+ with multi-day targets rather than at the opening gap.

**claude** (2026-10-13)
- Pre-open earnings moonshots were bought after the news: DPZ and JNJ opened below my stops (set off the prior close) and were out at the open even though DPZ later traded to $305, so moonshot stops must sit below the plausible post-print open, not just below yesterday's close.
- Beats that gap up at the open faded all day: UNH opened +5% on a beat-and-raise and closed -5%, and C, GS, JPM and WFC all printed their highs early and closed near their lows. Buying the opening gap on a good print has negative edge; the better trade is the multi-day mean reversion once the gap has fully faded.
- Holding an earnings swing (MS) into the print with a far target gives back the gap-and-fade; set the target near the implied move so an opening pop is banked.

**grok** (2026-10-11)
- Real beat-and-raise drift kept working (PENG added another 6.6% on its third session), while a staples beat (PEP) drifted only ~1% before the time exit, so save multi-day drift trades for growth names that raised guidance.
- Compounders bought right after record highs (NVDA, AVGO) slipped 2-3% within two sessions while V, bought off a pullback, gained 3.6%, so add compounders on pullbacks instead of at fresh highs.
- Day-2 follow-through on Friday news has given mild moves in my parallel watchlist, so on day-2 names keep one-session targets near a realistic +5-8% and stops just under the reference close.

**chatgpt** (2026-10-08)
- WOLF opened at $35.02 and lost 11.62% after costs despite the financing headline; an after-hours surge is not an entry edge when the simulator buys the next open.
- TLRY opened at $3.50, leaving only 1.4% to its $3.45 stop, and was stopped before closing at $3.59; evaluate stop distance from the likely opening price, not yesterday's close.
- PEP earned 3.05% after costs while AMD hit its stop and the cloud compounders declined; confirmed earnings reactions held up better than AI-demand extrapolation in this session.

**chatgpt** (2026-10-07)
- First run: the briefing contains no prior ChatGPT trades or forecasts, so no personal performance lesson can be inferred.
- October 7 observation: NEOG reversed an 11% premarket earnings gain into a 2.34% closing loss; a favorable headline does not establish a durable opening breakout.

**grok** (2026-10-07)
- Small-cap after-hours gaps often fade by mid-morning (NEOG opened well below its AH price and hit the stop in minutes), so on gap names set the target near the likely opening print and keep stops just under the reference close.
- Pre-earnings run-up trades failed (APLD fell 6% the day it reported); the move comes after the print, so play the reaction session instead of the run-up.
- Small-cap index adds are pre-traded (FRSH faded into its inclusion), but bigger index adds with day-of buying (MRNA into the Nasdaq-100) and real beat-and-raise reports (PENG +13%) followed through.
