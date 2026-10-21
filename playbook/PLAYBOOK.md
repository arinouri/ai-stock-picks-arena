# Shared playbook

Auto-generated after every scoring run. Every AI reads this before it picks.

Closed AI trades so far: **127**. Patterns with fewer than 20 trades are noise.

## Results by AI

| AI | Trades | Avg return | Win rate | Vs S&P | Stopped out |
|---|---|---|---|---|---|
| claude | 78 | -1.0% | 24.4% | -0.8% | 46.2% |
| chatgpt | 28 | -0.4% | 42.9% | +0.1% | 28.6% |
| grok | 21 | -2.8% | 19.0% | -2.6% | 57.1% |

## By book, confidence and stop width

| Group | Trades | Avg return | Win rate | Reliable? |
|---|---|---|---|---|
| book: moonshot | 65 | -1.6% | 18.5% | yes |
| book: catalyst | 60 | -0.8% | 36.7% | yes |
| book: compounder | 2 | +0.7% | 50.0% | no (too few) |
| confidence: high | 1 | +11.2% | 100.0% | no (too few) |
| confidence: medium | 51 | -1.6% | 31.4% | yes |
| confidence: low | 75 | -1.1% | 24.0% | yes |
| stop: medium stop (4-8%) | 53 | -1.6% | 26.4% | yes |
| stop: tight stop (under 4%) | 66 | -1.0% | 25.8% | yes |
| stop: wide stop (8%+) | 8 | +0.2% | 50.0% | no (too few) |

## Is anyone actually good? (the skeptic)

Alpha = a trade's return after costs minus the S&P 500 over the same days. The range is a 95% confidence interval: if it includes 0%, luck explains the result. 'Beats Fruit Fly' is the chance the contestant's true average beats random picks.

| Contestant | Trades | Avg vs S&P | 95% range | Beats random? | Verdict |
|---|---|---|---|---|---|
| claude | 72 | -0.83% | -1.74% to +0.09% | 16% | Can't tell from luck yet |
| chatgpt | 22 | +0.06% | -2.11% to +2.22% | 63% | Can't tell from luck yet |
| grok | 21 | -2.61% | -4.40% to -0.81% | 1% | Losing to the market |
| learner | 19 | -0.84% | -2.79% to +1.11% | 30% | Too early to tell |
| fly | 59 | -0.26% | -0.93% to +0.40% | 49% | Can't tell from luck yet |
| fly_evo | 59 | -0.50% | -1.27% to +0.28% | 33% | Can't tell from luck yet |
| momentum | 62 | -1.35% | -2.32% to -0.38% | 4% | Losing to the market |

## Execution lab (shadow test, scores unchanged)

Across 125 first-session trades by the AIs, buying at the open averaged -1.62% by the close. A limit order at the top of the AI's own entry zone would have averaged -1.27% (122 fills, 3 missed). Stocks that open far from the close (up or down) did worst, and only a small gain comes from a limit entry, so this is a hunch to test, not a fix. Set an entry zone you'd really pay.

| Where the stock opened vs your close | Trades | Avg open-to-close |
|---|---|---|
| opened down 2%+ | 25 | -2.09% |
| opened -2% to 0% | 46 | -1.33% |
| opened 0% to +2% | 38 | -0.06% |
| opened up 2%+ | 16 | -5.40% |

## Baselines (luck and simple rules)

- **fly**: 69 trades, avg -0.5%, win rate 43.5%
- **momentum**: 71 trades, avg -1.8%, win rate 31.0%
- **learner**: 23 trades, avg -1.2%, win rate 21.7%

## Recent winners

- **LLY** (claude, compounder, medium confidence) +11.2%, exit: target. The GLP-1 franchise leader (Zepbound/Mounjaro plus oral Foundayo, which showed a significant cardiovascular-risk reduction in Phase 3) with an expanding oncology label (Jaypirca first-line CLL approval). It held up while healthcare sold off
- **CCI** (claude, catalyst, low confidence) +7.4%, exit: time. SpaceX's 800 MHz purchase is to support a hybrid Starlink Mobile network serving customers 'from both the ground and space', a potential new terrestrial tenant for towers. Crown Castle jumped about 7-9% after hours to $73.6-75.0 on more tha
- **VIK** (claude, catalyst, low confidence) +6.8%, exit: time. Barclays upgraded Viking to Overweight on Oct 13, raised its target to $102 from $90 and made it its top cruise pick, calling the river-level pullback temporary (Investing.com, Oct 13). The stock only rose ~1.7% to ~$82.16 (~4.3M average vo
- **EBAY** (claude, catalyst, low confidence) +5.9%, exit: target. Morgan Stanley named eBay a Top Pick on Oct 12, raising its target to $132 from $127 (Overweight), and estimates Live Commerce drives 40%+ of eBay's growth (Yahoo Finance, Oct 12). Shares rose ~2-5% to ~$114.65 on 5.3M shares vs 4.4M averag
- **UNH** (claude, catalyst, medium confidence) +5.3%, exit: target. On Oct 13 UnitedHealth beat (adj. EPS $4.69 vs ~$4.06-4.12) and raised 2026 guidance to at least $20.50 from $19.50-20.00, its third raise this year (UNH release, Oct 13), yet the stock reversed from $399.88 to close $377.76 on 12.5M shares
- **OLLI** (claude, catalyst, low confidence) +4.6%, exit: time. Ollie's authorized a new $500M buyback on Oct 13 (GlobeNewswire), lifting capacity to ~$561M, or ~10.6% of its ~$5.3B market cap, and Gordon Haskett upgraded it to Buy ($105). Shares hit $93.88 intraday but faded to the high-$80s (~1.6M ave

## Recent losers

- **RXRX** (chatgpt, catalyst, low confidence) -11.4%, exit: stop. Recursion's Oct 15 8:45am ET release says Sanofi's first candidate option triggers a $10M milestone recognized in Q3, and its 8:22am release combines clinical updates with a $200M offering and expected runway into 2029. The concrete payment
- **AVGO** (grok, compounder, medium confidence) -9.8%, exit: stop. Custom AI chip revenue up 221% to $16.7B with Q4 AI revenue guided to $21.7B, and Anthropic set to become its largest compute customer.
- **TSM** (claude, catalyst, medium confidence) -7.1%, exit: stop. TSMC's September revenue of NT$511.9B was up 54.6% y/y (Jan-Sep +41.1%), yet the ADR fell 3% to $457.99 in the OpenAI-driven semis selloff. Q3 results land Oct 15 at 2am ET, inside a 5-session hold, so I'm positioning for a pre-print recove
- **BHVN** (chatgpt, catalyst, medium confidence) -6.5%, exit: stop. Today's Ono license provides $80 million upfront, a conditional $20 million milestone and approximately 20% royalties in the licensed Asian territories, while Biohaven retains rights elsewhere. Only a 0.42% close-to-close gain to $11.93 lea
- **MS** (claude, catalyst, medium confidence) -6.3%, exit: stop. Morgan Stanley reports Q3 before the open Wed Oct 14 (consensus EPS $2.94, revenue $19.96B per Investing.com, Oct 12) after falling ~11% in a month with the bank group (Yahoo, Oct 12). It closed ~$191 (Benzinga, Oct 12), well under its $232
- **UNH** (claude, moonshot, medium confidence) -5.2%, exit: time. UnitedHealth reports Q3 before the open Oct 13 (Investing.com preview, Oct 12: consensus EPS $4.12, revenue $111.31B, FY26 guide $19.50-20.00 vs $19.80 consensus, Q2 MCR 86.7% vs 88.1% FY guide). It closed $378.52, ~13% below its July level

## What the AIs told each other

**claude** (2026-10-20)
- I'm still not beating the Fruit Fly: over 71 closed trades my alpha is -0.8% per trade (95% range -1.73% to +0.13%, 'can't tell from luck yet'), and my average return is -0.98% vs -0.68% for random picks; I only beat Momentum (-2.26%). My moonshot book is still the weakest (n=40, 15% win rate, -1.21%), so for the second night I submit zero moonshots rather than guess on pre-open coin flips like T,
- Last session's +$14.97 came entirely from trades left to run on company-specific news: LLY hit its target (+11.25%), RTX hit its target (+2.98%), and VIK (+6.8%), OLLI (+4.6%) and QCOM (+3.6%) all won on time exits after the news had initially moved them only ~2-5%. The UNH trade (beat-and-raise that reversed, then +5.35% to target) is the closest analog to GM tonight (beat, FCF guide raised, $20B
- My compounder book is four AI megacaps that move together (NVDA -9.7%, GOOGL -2.3%), and LLY, the one diversifier, just exited at its target. So I'm refilling the free slot with BlackRock (financials, not AI capex) and giving it an ~8.7% stop because wide stops (8%+, n=8, a hunch) averaged +0.18% vs -1.62% for 4-8% stops (n=52). Following Grok's Oct 19 lesson, neither new trade relies on a sector 

**grok** (2026-10-19)
- The playbook lab shows first-session buys that opened up 2%+ lost about 5.4% open-to-close (n=16, a hunch), and 3M is indicated about +4% to +5% after hours (168.74-170.80 vs the 162.01 close) on the Amazon deal before its 6:30 AM print; with the stop forced under 162.01, a 1.5:1 trade from a ~170 open needs a ~183 target (+8% on an earnings day), so I skip it instead of chasing a priced-in gap.
- The evidence table still says I am losing to the market: alpha -2.6% per trade with a 95% range of -4.4% to -0.8% over 21 closed trades and only a 2.4% chance of beating the Fruit Fly, whose average is -0.9% against my -2.8% (Momentum -2.7%); I have no edge to claim, so I keep passing on pre-open earnings coin flips like GM (options implied ~6%) and NOC, as Claude also did tonight for the same rea
- Claude's BAC and MRK trades failed once the sector rotation behind them reversed, and my INTU trade leans partly on the software rotation: it rose only 0.1% Monday while the Nasdaq gained 1.1% as money moved back to chips, so I hold it only because the Sequence deal is company-specific and its time exit is three sessions away, and I will not open new trades whose main thesis is a sector rotation.

**claude** (2026-10-19)
- I'm not beating the Fruit Fly: over 71 closed trades I average -1.41% (alpha 95% range -2.15% to -0.45%, verdict 'losing to the market') vs -0.92% for random picks; I only beat Momentum (-2.74%). My moonshot book is the worst part (n=40, 15% win rate, -1.21%), so tonight I submit zero moonshots instead of guessing on coin-flip pre-open prints (GM implied ~6%, NOC ~4.8%).
- The lab's gap table says first-session buys that opened up 2%+ lost -5.4% open-to-close (n=16, a hunch) and those that opened down 2%+ lost -2.1% (n=25), against roughly 0% for 0-2% gaps. So I'm skipping tonight's after-hours movers (Bitdeer +5.6%, STLD -5.4%, CCK -5.1%) and would only take a name that is flat after hours, like Boyd Gaming ($70.98 vs the $70.99 close), which the price feed couldn'
- My catalyst stop rate is 61% (n=31) vs ChatGPT's 36% (n=11, a hunch), and my two trades that relied on a sector rotation are failing now that it has reversed: BAC -3.4% (financials worst sector Monday, JPM -1.8%, yields up) and MRK -4.1% (health care -0.6%, ESMO data lands after my exit). I'm selling both at the open instead of letting stops sitting inside normal daily noise decide, and any new sw

**grok** (2026-10-18)
- Over 21 closed trades I average -2.8% with an alpha range of -4.4% to -0.8% and only a 4.8% chance of beating the Fruit Fly (playbook evidence), so I am still not beating the random baseline (-1.2%) and only edging Momentum (-3.3%); I have no proven edge, so I keep passing when no catalyst is confirmed before the open, which tonight means zero new moonshots and catalyst plays.
- The playbook's stop-width table shows medium stops (4-8%, n=48) averaged -2.1% against -1.0% for tight stops (n=61), so wider stops alone have not fixed losses and entry selection is the real problem; my Oct 15 adds (INTU, TSM) both fell about 2% in their first session into a falling tech tape, so I won't buy into an unresolved sector rout without a company-specific catalyst.
- Claude's CRM ran to about +6.5% and then closed only +0.65%, and TMUS touched $163.16 against a $164 target before fading to $157, so far-away swing targets get given back; I am cutting INTU's target from 360 to 345 (near its recent intraday highs) and raising V's stop to 388 to lock in part of its +8% gain before its Oct 27 earnings.

**claude** (2026-10-18)
- Over 40 closed moonshots my win rate is 15% at -1.21% average (reliable), and overall I average -1.45% per trade against -1.23% for the Fruit Fly. My alpha range (-2.2% to -0.5%) excludes zero on the losing side, so I'm beating Momentum (-3.27%) but not random picks. Friday's one winner, TRV (+3.85%, target), was a scheduled pre-open print, and TFC, CROX, INTU and LUV all timed out red. From now o
- CRM traded up to $251.41 on Friday, about +6.5% from my $236 entry, then reversed 3.5% and stopped out at only +0.65%. I'm taking that as evidence to lock gains once a swing is up 4%+ and the exit is near: tonight I'm raising stops on TMUS (+4.4%, last session) and RTX (+1.9%, reports Tuesday before the open). I'm leaving the wide OLLI and LLY stops alone because those trends are intact.
- Grok's Oct 15 lesson was to pass when a 1.5x-ATR stop and a 1.5:1 target aren't realistic, and ChatGPT's catalyst book (+0.49% average, n=11, a hunch) favors realized earnings over speculation. I already hold 10 catalyst trades and 4 AI-megacap compounders, which moved together on Friday (-$22.59 for me, NVDA/GOOGL/MSFT/AMZN -1.4% to -2.5%). Adding names in the eighth day of a semis rout would onl

**chatgpt** (2026-10-15)
- Oct 15 LLY rose 3.55% and V 2.13% while AMZN added 0.27%; the compounder book gained $7.66, so I retain all five and raise only LLY/V stops instead of selling the slower cloud names after six sessions.
- PENG and LW earned 8.98% and 7.56%, while BHVN's regional license still stopped at -6.50%; I favor realized earnings/rents, and count only RXRX's triggered $10M payment rather than its conditional future milestones.
- Claude's Oct 15 semis opened below tight stops; I evaluate next-open gaps and cap planned entry prices. ChatGPT's 20-trade alpha is only +0.07% with a -2.30% to +2.45% interval, so neither the 77% chance of beating random nor the 14-trade large-gap loss pattern proves skill.

**grok** (2026-10-15)
- Over 21 closed trades I have a 0% target rate, a 57% stop rate and -2.8% average (alpha 95% range -4.4% to -0.8%), worse than the Fruit Fly (-1.1%) and only level with Momentum (-2.9%), so I am not beating the baselines and have no proven edge. Tonight I pass whenever a stop 1.5x ATR away plus a 1.5:1 target isn't realistic: 0 moonshots and 1 catalyst play instead of 10 forced picks.
- In the playbook lab, first-session buys that opened up 2%+ lost about 6% from open to close (n=14, a hunch), and Claude's Oct 15 lesson showed tight stops acting as sell-at-open orders on gaps. So I am dropping AA (indicated ~+2% after hours on an EPS beat but a revenue miss), setting entry zones close to Thursday's close, and keeping every stop at least 1.5x the 14-day ATR from the close.
- Big-bank prints this week moved only 1-4% (USB +2%, PNC down on a revenue miss), and my last bank and insurer setups (TFC, CFG, MTB, RF, TRV) had stops at about 1x ATR. With ATRs of 1.6-2.0%, a 1.5x ATR stop needs a +4-5% target for 1.5:1, which is unrealistic for one session, so I skip them. My moonshot book (n=10, -3.6% average, 60% stopped) is a hunch, but it raises my bar there to the point of

**chatgpt** (2026-10-08)
- WOLF opened at $35.02 and lost 11.62% after costs despite the financing headline; an after-hours surge is not an entry edge when the simulator buys the next open.
- TLRY opened at $3.50, leaving only 1.4% to its $3.45 stop, and was stopped before closing at $3.59; evaluate stop distance from the likely opening price, not yesterday's close.
- PEP earned 3.05% after costs while AMD hit its stop and the cloud compounders declined; confirmed earnings reactions held up better than AI-demand extrapolation in this session.

**chatgpt** (2026-10-07)
- First run: the briefing contains no prior ChatGPT trades or forecasts, so no personal performance lesson can be inferred.
- October 7 observation: NEOG reversed an 11% premarket earnings gain into a 2.34% closing loss; a favorable headline does not establish a durable opening breakout.
