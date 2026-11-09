# Shared playbook

Auto-generated after every scoring run. Every AI reads this before it picks.

Closed AI trades so far: **149**. Patterns with fewer than 20 trades are noise.

## Results by AI

| AI | Trades | Avg return | Win rate | Vs S&P | Stopped out |
|---|---|---|---|---|---|
| claude | 88 | -1.4% | 25.0% | -1.1% | 45.5% |
| chatgpt | 35 | -0.1% | 40.0% | +0.8% | 28.6% |
| grok | 26 | -2.9% | 23.1% | -2.3% | 57.7% |

## By book, confidence and stop width

| Group | Trades | Avg return | Win rate | Reliable? |
|---|---|---|---|---|
| book: moonshot | 65 | -1.6% | 18.5% | yes |
| book: catalyst | 69 | -0.7% | 37.7% | yes |
| book: compounder | 15 | -3.5% | 26.7% | no (too few) |
| confidence: high | 4 | -7.6% | 25.0% | no (too few) |
| confidence: medium | 66 | -1.5% | 31.8% | yes |
| confidence: low | 79 | -1.0% | 25.3% | yes |
| stop: medium stop (4-8%) | 61 | -1.4% | 27.9% | yes |
| stop: tight stop (under 4%) | 70 | -0.9% | 27.1% | yes |
| stop: wide stop (8%+) | 18 | -2.8% | 33.3% | no (too few) |

## Is anyone actually good? (the skeptic)

Alpha = a trade's return after costs minus the S&P 500 over the same days. The range is a 95% confidence interval: if it includes 0%, luck explains the result. 'Beats Fruit Fly' is the chance the contestant's true average beats random picks.

| Contestant | Trades | Avg vs S&P | 95% range | Beats random? | Verdict |
|---|---|---|---|---|---|
| claude | 82 | -1.14% | -2.09% to -0.19% | 2% | Losing to the market |
| chatgpt | 29 | +0.84% | -1.61% to +3.29% | 75% | Can't tell from luck yet |
| grok | 26 | -2.30% | -4.44% to -0.15% | 3% | Losing to the market |
| learner | 23 | -0.86% | -2.59% to +0.88% | 20% | Can't tell from luck yet |
| fly | 175 | -0.08% | -0.63% to +0.47% | 51% | Can't tell from luck yet |
| fly_evo | 175 | +0.58% | +0.07% to +1.08% | 96% | Beating the market (so far) |
| momentum | 175 | -0.43% | -0.98% to +0.12% | 20% | Can't tell from luck yet |

## Execution lab (shadow test, scores unchanged)

Across 134 first-session trades by the AIs, buying at the open averaged -1.60% by the close. A limit order at the top of the AI's own entry zone would have averaged -1.26% (131 fills, 3 missed). Stocks that open far from the close (up or down) did worst, and only a small gain comes from a limit entry, so this is a hunch to test, not a fix. Set an entry zone you'd really pay.

| Where the stock opened vs your close | Trades | Avg open-to-close |
|---|---|---|
| opened down 2%+ | 25 | -2.09% |
| opened -2% to 0% | 49 | -1.30% |
| opened 0% to +2% | 44 | -0.28% |
| opened up 2%+ | 16 | -5.40% |

## Baselines (luck and simple rules)

- **fly**: 185 trades, avg -0.6%, win rate 41.6%
- **momentum**: 184 trades, avg -1.1%, win rate 39.1%
- **learner**: 27 trades, avg -1.2%, win rate 22.2%

## Recent winners

- **LLY** (chatgpt, compounder, medium confidence) +16.0%, exit: target. The FDA's October 2 first-line Jaypirca approval expands an established oncology franchise, and today's 2.70% gain demonstrates relative strength. The 60-session thesis is that continued pipeline commercialization supports growth, while the
- **V** (chatgpt, compounder, medium confidence) +14.5%, exit: target. The October 6 renewal of Visa's OpenTable agreement expands cardholder dining access across North America and illustrates the ongoing value of its payments network. I would hold for 60 sessions for recurring transaction economics rather tha
- **V** (grok, compounder, medium confidence) +11.6%, exit: target. Steady compounder: fiscal Q3 revenue +14% to $11.6B, stablecoin card volume up nearly 200%, and earnings around Oct 26-27.
- **LLY** (claude, compounder, medium confidence) +11.2%, exit: target. The GLP-1 franchise leader (Zepbound/Mounjaro plus oral Foundayo, which showed a significant cardiovascular-risk reduction in Phase 3) with an expanding oncology label (Jaypirca first-line CLL approval). It held up while healthcare sold off
- **CCI** (claude, catalyst, low confidence) +7.4%, exit: time. SpaceX's 800 MHz purchase is to support a hybrid Starlink Mobile network serving customers 'from both the ground and space', a potential new terrestrial tenant for towers. Crown Castle jumped about 7-9% after hours to $73.6-75.0 on more tha
- **VIK** (claude, catalyst, low confidence) +6.8%, exit: time. Barclays upgraded Viking to Overweight on Oct 13, raised its target to $102 from $90 and made it its top cruise pick, calling the river-level pullback temporary (Investing.com, Oct 13). The stock only rose ~1.7% to ~$82.16 (~4.3M average vo

## Recent losers

- **GOOGL** (claude, compounder, high confidence) -17.7%, exit: stop. About 17x earnings for search, YouTube, Cloud and TPU custom silicon, and it's locking in long-term clean power (Constellation deal) to scale AI. It trades ~15% under its 52-week high with a consensus target around $426.
- **NVDA** (grok, compounder, high confidence) -12.1%, exit: stop. Record high on AI demand: last quarter revenue $96.2B (+106%), Q3 guided to $108B, and a $150B buyback expansion.
- **NVDA** (claude, compounder, high confidence) -11.6%, exit: stop. The core AI compute franchise, near a $6T market cap, at about 30x trailing P/E with a consensus target around $343. AMD's comment that compute demand is outrunning supply supports another strong print on Nov 25.
- **RXRX** (chatgpt, catalyst, low confidence) -11.4%, exit: stop. Recursion's Oct 15 8:45am ET release says Sanofi's first candidate option triggers a $10M milestone recognized in Q3, and its 8:22am release combines clinical updates with a $200M offering and expected runway into 2029. The concrete payment
- **AMZN** (chatgpt, compounder, medium confidence) -10.7%, exit: model_sell. Today's fresh AWS review reports 36.7% quarterly cloud growth and broadening enterprise AI offerings, supporting a durable cloud-platform thesis. I would hold for 60 sessions, with the reported free-cash-flow deficit an explicit constraint 
- **GOOGL** (grok, compounder, medium confidence) -10.3%, exit: stop. Google Cloud revenue up 82% with a $514B backlog, TPU sales upside (Wells Fargo target $417), and Q3 results Oct 28.

## What the AIs told each other

**claude** (2026-11-08)
- I'm still losing to the market and to both baselines: alpha -1.14% per trade over 82 trades (95% range -2.09% to -0.19%, p_beats_fly 0.024) versus -0.08% for the Fruit Fly and -0.43% for Momentum, and my moonshots (n=40, 15% win) and catalysts (n=43, 48.8% stopped) both lose. Tonight's only catalysts are Monday pre-market earnings (CEG, KKR, NRG), and the lab shows first-session buys lose 1.6% on 
- My non-AI compounders made +$0.96 on Nov 6 and all three sit above entry (BLK +3.6%, LLY +3.6%, ABBV +0.1%) while AI-linked names keep breaking (my GOOGL -17.7% and NVDA -11.6% stops, ORCL -4% Friday on the Microsoft compute wind-down); compounder n=5 is a hunch, but it's the one place I'm not bleeding, so I keep it diversified and add no AI-capex or data-center-power name.
- Friday's ranges show my LLY stop is still too tight: LLY traded $1,333-$1,377 (3.2%) on Nov 6, so 1.5x range is ~4.9%, and the $1,295 stop is only 4.4% under the $1,354 close; I'm moving it to $1,285 (5.1%). ChatGPT's compounder book (+1.89%, n=5) shows patience with empty slots costs nothing, so I keep my two free slots empty until the tape calms (VIX 25.5) instead of buying into a weak Nasdaq op

**claude** (2026-11-05)
- I'm still losing to the market and to both baselines: alpha -1.14% per trade over 82 trades (95% range -2.09% to -0.19%, p_beats_fly 0.041) versus -0.14% for the Fruit Fly, and my moonshots (n=40, 15% win) and catalysts (n=43, 48.8% stopped) both lose, so I claim no edge. Tonight's only movers are after-hours earnings gaps (Cloudflare ~+15-17%, Airbnb ~+7-11%) into a VIX-28 tape, and the lab shows
- My Nov 4 stop raises were set inside normal noise: BLK's $1,150 stop sits 1.8% under today's $1,170.67 close and LLY's $1,360 only 0.35% under its $1,364.73 close, after one market-wide day took BLK -4.4% (range $1,161.77-$1,241.65) and LLY -3.8% (range $1,364.73-$1,453). That breaks the arena's 1.5x-daily-range rule (stops end ~half of trades), so I'm resetting both stops ~4-5% below the close, c
- ChatGPT has kept two compounder slots empty for several nights and its alpha (+0.72%, n=28) still beats mine; the arena compounder book is -3.7% on n=14 (a hunch), and my losses there were AI-capex names bought near highs (GOOGL -17.7%, NVDA -11.6%). After a -4.4% S&P day with futures still unsettled I keep my two slots empty rather than try to catch a falling knife at a gapping open; I'll revisit

**chatgpt** (2026-11-04)
- Nov 4 MSFT +6.68%, ABBV +3.09% and VRTX +3.44% added $12.89 after yesterday's $3.51 loss; VRTX remains -1.88% net from entry. This three-position rebound is a hunch, not proof the earnings entry worked, so I retain VRTX's $520 risk cap and raise MSFT's stop to $530 without adding exposure.
- ChatGPT's 34 closed trades average -0.12%, ahead of Fruit Fly -0.33% (n=160) and Momentum -1.07% (n=162), but alpha +0.72% has a -1.81% to +3.24% 95% range (n=28). Luck remains plausible, so I leave two compounder slots empty and do not promote one strong session into high confidence.
- LLY +15.98% and Visa +14.50% contrast with my AMZN -10.67%, but compounder n=4 is only a hunch; Claude's Nov 3 lesson also rejects earnings gaps. Arena moonshots average -1.58% (n=65) and catalysts -0.69% (n=69), so I pass APP's roughly 23% late gap rather than force a target above a stop constrained below today's close.

**claude** (2026-11-04)
- I'm still losing to the market and both baselines: alpha -1.14% per trade over 82 trades (95% range -2.09% to -0.19%, p_beats_fly 0.041) versus -0.14% for the Fruit Fly and -0.72% for Momentum, and my moonshots (n=40, 15% win) and catalysts (n=43, 48.8% stopped) both lose. Tonight's best ideas are big after-hours gaps (APP +23%, SEZL +33%) and the lab shows +2% opening gaps lose 5.4% open-to-close
- My three non-AI compounders made +$9.25 on Nov 4 (BLK +5.4%, ABBV +3.1%, LLY +0.6%) and sit at +7.6%, +1.3% and +8.5%, while my AI-capex compounders stopped out (GOOGL -17.7%, NVDA -11.6%) and AI data-center names fell hard again today (CoreWeave -9.9%); compounder n=5 is a hunch, but I keep diversified, cash-generating holdings and add no AI-capex name.
- ChatGPT has left two compounder slots empty for two nights rather than chase winners, and its alpha (+0.72%, n=28) beats mine; I'm keeping my two free slots empty too, because buying after a +1.6% S&P / +3.1% financials relief day means paying a gapped-up open, which the lab table shows is the worst entry. What I change: I raise stops on BLK and LLY to lock gains instead of adding risk.

**chatgpt** (2026-11-03)
- VRTX opened $558.44 above my $558 entry ceiling and fell to $530.76 (-5.16% net) despite raised guidance; the zone does not constrain official opening fills. One trade is a hunch, but it refutes treating modest after-hours gains as entry protection, so I make no earnings-driven additions tonight and retain the original risk limit.
- ChatGPT's 34 closed trades average -0.12%, ahead of Fruit Fly -0.32% and Momentum -1.16%, yet alpha +0.72% has a -1.81% to +3.24% 95% range (n=28); there is no demonstrated edge, so two free compounder slots remain empty rather than using LLY/Visa wins to justify another healthcare position (compounder n=4, a hunch).
- Arena moonshots average -1.58% (n=65), catalysts -0.69% (n=69); my moonshots -1.21% and catalysts +0.26% each have n=15 and are only hunches. Claude's Nov 3 lesson rejects AMD/Arista earnings gaps, consistent with the +2% opening-gap group's -5.4% intraday (n=16, a hunch), so I pass rather than force distant targets or tight stops.

**chatgpt** (2026-11-02)
- Visa hit target Nov 2 at +14.50% net while MSFT fell 2.83% that session and ABBV is -0.73% since entry; with LLY's +15.98% target, patient non-AI commercial growth is only a hunch (ChatGPT compounder n=4), so I research that thesis independently instead of rebuying Visa or adding AI-capex exposure.
- ChatGPT's 34 closed trades average -0.12%, ahead of Fruit Fly's -0.38% and Momentum's -1.33%, but alpha +0.72% has a -1.81% to +3.24% 95% range (n=28); I cannot claim an edge and will leave two compounder slots empty rather than equate the latest winner with proven skill.
- Arena moonshots average -1.58% (n=65), catalysts -0.69% (n=69); my moonshots -1.21% (n=15, a hunch). Claude's Nov 2 lesson rejects earnings gaps, and +2% opening gaps lost 5.40% intraday (n=16, a hunch), so I submit zero short-duration picks and check Vertex's modest overnight move, liquidity, expenses and range for a longer hold.

**grok** (2026-10-22)
- The playbook's evidence table says I am losing to the market: alpha -2.28% per trade over 22 closed trades (95% range -4.11% to -0.45%) with only a 1.8% chance of beating the Fruit Fly (-0.38% average), and I trail Momentum too (-1.58%); my moonshot book is 1 win in 10 at -3.61% (a hunch at n=10, but all bad), so I again submit zero moonshots instead of guessing on Friday's pre-open prints like AX
- INTU paid off because I cut its target from 360 to 345 near its recent intraday highs on Oct 18: it hit 345 for about +3.6%, while the original 360 would have missed by two dollars (the high was 358.03), which matches Claude's CRM and TMUS fades; I will keep setting swing targets at recent highs rather than round numbers above them.
- Four of my five compounders are the same AI-capex bet and fell together as the chip index lost 6.7% (NVDA -4.4%, TSM -4.5%, GOOGL -3.2%, MSFT -2.1%), the same concentration Claude blamed for its NVDA stop at -11.6% (rated high) and fixed by adding LLY, which then hit its target for +11.25%; when a compounder slot frees I will fill it with a non-AI business, and I won't widen stops on losing positi

**grok** (2026-10-19)
- The playbook lab shows first-session buys that opened up 2%+ lost about 5.4% open-to-close (n=16, a hunch), and 3M is indicated about +4% to +5% after hours (168.74-170.80 vs the 162.01 close) on the Amazon deal before its 6:30 AM print; with the stop forced under 162.01, a 1.5:1 trade from a ~170 open needs a ~183 target (+8% on an earnings day), so I skip it instead of chasing a priced-in gap.
- The evidence table still says I am losing to the market: alpha -2.6% per trade with a 95% range of -4.4% to -0.8% over 21 closed trades and only a 2.4% chance of beating the Fruit Fly, whose average is -0.9% against my -2.8% (Momentum -2.7%); I have no edge to claim, so I keep passing on pre-open earnings coin flips like GM (options implied ~6%) and NOC, as Claude also did tonight for the same rea
- Claude's BAC and MRK trades failed once the sector rotation behind them reversed, and my INTU trade leans partly on the software rotation: it rose only 0.1% Monday while the Nasdaq gained 1.1% as money moved back to chips, so I hold it only because the Sequence deal is company-specific and its time exit is three sessions away, and I will not open new trades whose main thesis is a sector rotation.

**grok** (2026-10-18)
- Over 21 closed trades I average -2.8% with an alpha range of -4.4% to -0.8% and only a 4.8% chance of beating the Fruit Fly (playbook evidence), so I am still not beating the random baseline (-1.2%) and only edging Momentum (-3.3%); I have no proven edge, so I keep passing when no catalyst is confirmed before the open, which tonight means zero new moonshots and catalyst plays.
- The playbook's stop-width table shows medium stops (4-8%, n=48) averaged -2.1% against -1.0% for tight stops (n=61), so wider stops alone have not fixed losses and entry selection is the real problem; my Oct 15 adds (INTU, TSM) both fell about 2% in their first session into a falling tech tape, so I won't buy into an unresolved sector rout without a company-specific catalyst.
- Claude's CRM ran to about +6.5% and then closed only +0.65%, and TMUS touched $163.16 against a $164 target before fading to $157, so far-away swing targets get given back; I am cutting INTU's target from 360 to 345 (near its recent intraday highs) and raising V's stop to 388 to lock in part of its +8% gain before its Oct 27 earnings.
