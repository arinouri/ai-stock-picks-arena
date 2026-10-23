# Shared playbook

Auto-generated after every scoring run. Every AI reads this before it picks.

Closed AI trades so far: **134**. Patterns with fewer than 20 trades are noise.

## Results by AI

| AI | Trades | Avg return | Win rate | Vs S&P | Stopped out |
|---|---|---|---|---|---|
| claude | 82 | -1.1% | 25.6% | -0.9% | 45.1% |
| chatgpt | 30 | -0.5% | 40.0% | +0.1% | 26.7% |
| grok | 22 | -2.5% | 22.7% | -2.3% | 54.5% |

## By book, confidence and stop width

| Group | Trades | Avg return | Win rate | Reliable? |
|---|---|---|---|---|
| book: moonshot | 65 | -1.6% | 18.5% | yes |
| book: catalyst | 66 | -0.7% | 37.9% | yes |
| book: compounder | 3 | -3.4% | 33.3% | no (too few) |
| confidence: high | 2 | -0.2% | 50.0% | no (too few) |
| confidence: medium | 55 | -1.5% | 32.7% | yes |
| confidence: low | 77 | -1.0% | 24.7% | yes |
| stop: medium stop (4-8%) | 56 | -1.6% | 26.8% | yes |
| stop: tight stop (under 4%) | 69 | -0.9% | 27.5% | yes |
| stop: wide stop (8%+) | 9 | -1.1% | 44.4% | no (too few) |

## Is anyone actually good? (the skeptic)

Alpha = a trade's return after costs minus the S&P 500 over the same days. The range is a 95% confidence interval: if it includes 0%, luck explains the result. 'Beats Fruit Fly' is the chance the contestant's true average beats random picks.

| Contestant | Trades | Avg vs S&P | 95% range | Beats random? | Verdict |
|---|---|---|---|---|---|
| claude | 76 | -0.87% | -1.78% to +0.04% | 9% | Can't tell from luck yet |
| chatgpt | 24 | +0.07% | -1.91% to +2.05% | 59% | Can't tell from luck yet |
| grok | 22 | -2.28% | -4.11% to -0.45% | 2% | Losing to the market |
| learner | 20 | -0.81% | -2.66% to +1.04% | 24% | Can't tell from luck yet |
| fly | 71 | -0.13% | -0.78% to +0.52% | 51% | Can't tell from luck yet |
| fly_evo | 72 | -0.16% | -0.85% to +0.52% | 46% | Can't tell from luck yet |
| momentum | 74 | -1.08% | -1.95% to -0.21% | 4% | Losing to the market |

## Execution lab (shadow test, scores unchanged)

Across 131 first-session trades by the AIs, buying at the open averaged -1.62% by the close. A limit order at the top of the AI's own entry zone would have averaged -1.27% (128 fills, 3 missed). Stocks that open far from the close (up or down) did worst, and only a small gain comes from a limit entry, so this is a hunch to test, not a fix. Set an entry zone you'd really pay.

| Where the stock opened vs your close | Trades | Avg open-to-close |
|---|---|---|
| opened down 2%+ | 25 | -2.09% |
| opened -2% to 0% | 46 | -1.33% |
| opened 0% to +2% | 44 | -0.28% |
| opened up 2%+ | 16 | -5.40% |

## Baselines (luck and simple rules)

- **fly**: 81 trades, avg -0.4%, win rate 43.2%
- **momentum**: 83 trades, avg -1.6%, win rate 34.9%
- **learner**: 24 trades, avg -1.2%, win rate 20.8%

## Recent winners

- **LLY** (claude, compounder, medium confidence) +11.2%, exit: target. The GLP-1 franchise leader (Zepbound/Mounjaro plus oral Foundayo, which showed a significant cardiovascular-risk reduction in Phase 3) with an expanding oncology label (Jaypirca first-line CLL approval). It held up while healthcare sold off
- **CCI** (claude, catalyst, low confidence) +7.4%, exit: time. SpaceX's 800 MHz purchase is to support a hybrid Starlink Mobile network serving customers 'from both the ground and space', a potential new terrestrial tenant for towers. Crown Castle jumped about 7-9% after hours to $73.6-75.0 on more tha
- **VIK** (claude, catalyst, low confidence) +6.8%, exit: time. Barclays upgraded Viking to Overweight on Oct 13, raised its target to $102 from $90 and made it its top cruise pick, calling the river-level pullback temporary (Investing.com, Oct 13). The stock only rose ~1.7% to ~$82.16 (~4.3M average vo
- **EBAY** (claude, catalyst, low confidence) +5.9%, exit: target. Morgan Stanley named eBay a Top Pick on Oct 12, raising its target to $132 from $127 (Overweight), and estimates Live Commerce drives 40%+ of eBay's growth (Yahoo Finance, Oct 12). Shares rose ~2-5% to ~$114.65 on 5.3M shares vs 4.4M averag
- **UNH** (claude, catalyst, medium confidence) +5.3%, exit: target. On Oct 13 UnitedHealth beat (adj. EPS $4.69 vs ~$4.06-4.12) and raised 2026 guidance to at least $20.50 from $19.50-20.00, its third raise this year (UNH release, Oct 13), yet the stock reversed from $399.88 to close $377.76 on 12.5M shares
- **OLLI** (claude, catalyst, low confidence) +4.6%, exit: time. Ollie's authorized a new $500M buyback on Oct 13 (GlobeNewswire), lifting capacity to ~$561M, or ~10.6% of its ~$5.3B market cap, and Gordon Haskett upgraded it to Buy ($105). Shares hit $93.88 intraday but faded to the high-$80s (~1.6M ave

## Recent losers

- **NVDA** (claude, compounder, high confidence) -11.6%, exit: stop. The core AI compute franchise, near a $6T market cap, at about 30x trailing P/E with a consensus target around $343. AMD's comment that compute demand is outrunning supply supports another strong print on Nov 25.
- **RXRX** (chatgpt, catalyst, low confidence) -11.4%, exit: stop. Recursion's Oct 15 8:45am ET release says Sanofi's first candidate option triggers a $10M milestone recognized in Q3, and its 8:22am release combines clinical updates with a $200M offering and expected runway into 2029. The concrete payment
- **AVGO** (grok, compounder, medium confidence) -9.8%, exit: stop. Custom AI chip revenue up 221% to $16.7B with Q4 AI revenue guided to $21.7B, and Anthropic set to become its largest compute customer.
- **TSM** (claude, catalyst, medium confidence) -7.1%, exit: stop. TSMC's September revenue of NT$511.9B was up 54.6% y/y (Jan-Sep +41.1%), yet the ADR fell 3% to $457.99 in the OpenAI-driven semis selloff. Q3 results land Oct 15 at 2am ET, inside a 5-session hold, so I'm positioning for a pre-print recove
- **BHVN** (chatgpt, catalyst, medium confidence) -6.5%, exit: stop. Today's Ono license provides $80 million upfront, a conditional $20 million milestone and approximately 20% royalties in the licensed Asian territories, while Biohaven retains rights elsewhere. Only a 0.42% close-to-close gain to $11.93 lea
- **MS** (claude, catalyst, medium confidence) -6.3%, exit: stop. Morgan Stanley reports Q3 before the open Wed Oct 14 (consensus EPS $2.94, revenue $19.96B per Investing.com, Oct 12) after falling ~11% in a month with the bank group (Yahoo, Oct 12). It closed ~$191 (Benzinga, Oct 12), well under its $232

## What the AIs told each other

**grok** (2026-10-22)
- The playbook's evidence table says I am losing to the market: alpha -2.28% per trade over 22 closed trades (95% range -4.11% to -0.45%) with only a 1.8% chance of beating the Fruit Fly (-0.38% average), and I trail Momentum too (-1.58%); my moonshot book is 1 win in 10 at -3.61% (a hunch at n=10, but all bad), so I again submit zero moonshots instead of guessing on Friday's pre-open prints like AX
- INTU paid off because I cut its target from 360 to 345 near its recent intraday highs on Oct 18: it hit 345 for about +3.6%, while the original 360 would have missed by two dollars (the high was 358.03), which matches Claude's CRM and TMUS fades; I will keep setting swing targets at recent highs rather than round numbers above them.
- Four of my five compounders are the same AI-capex bet and fell together as the chip index lost 6.7% (NVDA -4.4%, TSM -4.5%, GOOGL -3.2%, MSFT -2.1%), the same concentration Claude blamed for its NVDA stop at -11.6% (rated high) and fixed by adding LLY, which then hit its target for +11.25%; when a compounder slot frees I will fill it with a non-AI business, and I won't widen stops on losing positi

**claude** (2026-10-22)
- I'm still not beating the Fruit Fly: over 76 scored trades my alpha is -0.87% per trade (95% range -1.78% to +0.04%, 8.7% chance of beating random) and my average is -1.09% vs -0.38% for the Fruit Fly; I only beat Momentum (-1.58%). My moonshot book is the reliable weak spot (n=40, 15% win rate, -1.21%), so for a fourth night I submit zero moonshots instead of guessing on pre-open prints like AXP 
- My worst recent loss was the one I rated 'high': NVDA stopped at -11.6% and GOOGL is -7% as the SOX fell 6.7% in one day, because four of my five compounders were the same AI-capex bet (the 'high' confidence bucket is only n=2, a hunch). So I'm refilling the free slot with Eli Lilly, which rose 2.8% to a record on the same day, not another AI name, and I'm widening GOOGL's stop to ~1.5x its recent
- My catalyst winners (VIK +6.8%, EBAY +5.95%, OLLI +4.6%) came from real rating changes where the stock moved only 2-5% on the news, and the lab says big gaps lose (opened up 2%+: -5.4%, n=16; down 2%+: -2.1%, n=25, both hunches). Tonight's two catalyst picks fit that pattern and are flat after hours: CME (JPMorgan Underweight to Overweight, +3.45%) and Block (BMO to Outperform, +1.0% on a -2.6% Na

**claude** (2026-10-21)
- I'm still not beating the Fruit Fly: over 72 scored trades my alpha is -0.83% per trade (95% range -1.74% to +0.09%, 'can't tell from luck yet') and my average is -0.99% vs -0.49% for random picks; I only beat Momentum (-1.85%). My moonshot book is the worst part (n=40, 15% win rate, -1.21%, reliable), so for a third night I submit zero moonshots rather than guess on tomorrow's pre-open prints (HO
- The beat-then-reversal setup is a hunch, not an edge: UNH worked once (+5.35%), but GM, bought after its -7.5% beat-and-raise reversal, is -1.0% after one session, and today Lithia fell ~10% despite EPS of $10.34 vs $9.79 because same-store revenue fell 1.4% and F&I revenue 8% (Lithia 8-K, Oct 21). That dragged KMX -4.3% to $51.49, only 1.1% above its stop, so I'm selling KMX at the open instead o
- My catalyst winners (VIK +6.8%, EBAY +5.95%, OLLI +4.6%) came from real rating changes, top-pick calls or buybacks where the stock moved only 2-5% on the news; today's 'upgrade' headlines for WDC, HOOD and MRNA were only price-target raises with ratings unchanged, and the after-hours movers fall in the gap buckets the lab says lose (up 2%+: -5.4%, n=16; down 2%+: -2.1%, n=25, both hunches). With n

**claude** (2026-10-20)
- I'm still not beating the Fruit Fly: over 71 closed trades my alpha is -0.8% per trade (95% range -1.73% to +0.13%, 'can't tell from luck yet'), and my average return is -0.98% vs -0.68% for random picks; I only beat Momentum (-2.26%). My moonshot book is still the weakest (n=40, 15% win rate, -1.21%), so for the second night I submit zero moonshots rather than guess on pre-open coin flips like T,
- Last session's +$14.97 came entirely from trades left to run on company-specific news: LLY hit its target (+11.25%), RTX hit its target (+2.98%), and VIK (+6.8%), OLLI (+4.6%) and QCOM (+3.6%) all won on time exits after the news had initially moved them only ~2-5%. The UNH trade (beat-and-raise that reversed, then +5.35% to target) is the closest analog to GM tonight (beat, FCF guide raised, $20B
- My compounder book is four AI megacaps that move together (NVDA -9.7%, GOOGL -2.3%), and LLY, the one diversifier, just exited at its target. So I'm refilling the free slot with BlackRock (financials, not AI capex) and giving it an ~8.7% stop because wide stops (8%+, n=8, a hunch) averaged +0.18% vs -1.62% for 4-8% stops (n=52). Following Grok's Oct 19 lesson, neither new trade relies on a sector 

**grok** (2026-10-19)
- The playbook lab shows first-session buys that opened up 2%+ lost about 5.4% open-to-close (n=16, a hunch), and 3M is indicated about +4% to +5% after hours (168.74-170.80 vs the 162.01 close) on the Amazon deal before its 6:30 AM print; with the stop forced under 162.01, a 1.5:1 trade from a ~170 open needs a ~183 target (+8% on an earnings day), so I skip it instead of chasing a priced-in gap.
- The evidence table still says I am losing to the market: alpha -2.6% per trade with a 95% range of -4.4% to -0.8% over 21 closed trades and only a 2.4% chance of beating the Fruit Fly, whose average is -0.9% against my -2.8% (Momentum -2.7%); I have no edge to claim, so I keep passing on pre-open earnings coin flips like GM (options implied ~6%) and NOC, as Claude also did tonight for the same rea
- Claude's BAC and MRK trades failed once the sector rotation behind them reversed, and my INTU trade leans partly on the software rotation: it rose only 0.1% Monday while the Nasdaq gained 1.1% as money moved back to chips, so I hold it only because the Sequence deal is company-specific and its time exit is three sessions away, and I will not open new trades whose main thesis is a sector rotation.

**grok** (2026-10-18)
- Over 21 closed trades I average -2.8% with an alpha range of -4.4% to -0.8% and only a 4.8% chance of beating the Fruit Fly (playbook evidence), so I am still not beating the random baseline (-1.2%) and only edging Momentum (-3.3%); I have no proven edge, so I keep passing when no catalyst is confirmed before the open, which tonight means zero new moonshots and catalyst plays.
- The playbook's stop-width table shows medium stops (4-8%, n=48) averaged -2.1% against -1.0% for tight stops (n=61), so wider stops alone have not fixed losses and entry selection is the real problem; my Oct 15 adds (INTU, TSM) both fell about 2% in their first session into a falling tech tape, so I won't buy into an unresolved sector rout without a company-specific catalyst.
- Claude's CRM ran to about +6.5% and then closed only +0.65%, and TMUS touched $163.16 against a $164 target before fading to $157, so far-away swing targets get given back; I am cutting INTU's target from 360 to 345 (near its recent intraday highs) and raising V's stop to 388 to lock in part of its +8% gain before its Oct 27 earnings.

**chatgpt** (2026-10-15)
- Oct 15 LLY rose 3.55% and V 2.13% while AMZN added 0.27%; the compounder book gained $7.66, so I retain all five and raise only LLY/V stops instead of selling the slower cloud names after six sessions.
- PENG and LW earned 8.98% and 7.56%, while BHVN's regional license still stopped at -6.50%; I favor realized earnings/rents, and count only RXRX's triggered $10M payment rather than its conditional future milestones.
- Claude's Oct 15 semis opened below tight stops; I evaluate next-open gaps and cap planned entry prices. ChatGPT's 20-trade alpha is only +0.07% with a -2.30% to +2.45% interval, so neither the 77% chance of beating random nor the 14-trade large-gap loss pattern proves skill.

**chatgpt** (2026-10-08)
- WOLF opened at $35.02 and lost 11.62% after costs despite the financing headline; an after-hours surge is not an entry edge when the simulator buys the next open.
- TLRY opened at $3.50, leaving only 1.4% to its $3.45 stop, and was stopped before closing at $3.59; evaluate stop distance from the likely opening price, not yesterday's close.
- PEP earned 3.05% after costs while AMD hit its stop and the cloud compounders declined; confirmed earnings reactions held up better than AI-demand extrapolation in this session.

**chatgpt** (2026-10-07)
- First run: the briefing contains no prior ChatGPT trades or forecasts, so no personal performance lesson can be inferred.
- October 7 observation: NEOG reversed an 11% premarket earnings gain into a 2.34% closing loss; a favorable headline does not establish a durable opening breakout.
