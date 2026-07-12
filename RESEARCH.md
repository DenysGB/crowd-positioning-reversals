# Crowded positioning and price reversals in perpetual futures

Denys Melnychuk

## 1. The question

**What is known.** Concentrated positioning unwinds badly: the crowded-trades and
predatory-trading literatures both argue that when many participants sit on the same side,
their exit is predictable and price moves against them. **What is missing.** Almost all of
that work has to infer positioning indirectly — from fund flows, from 13F filings, from
price action — because equity markets do not publish who holds what, and none of those
proxies say anything about how much leverage sits behind the position. **What I add.** I
test the claim on data that does publish it, and show the reversal is conditional: it
appears when leverage is accumulating and largely disappears when it isn't. Crowding by
itself does very little.

Perpetual futures give you something equity markets don't: a public, high-frequency
record of where the crowd actually is. Binance publishes the ratio of accounts holding
long versus short positions, updated every five minutes, going back years. That's an
unusually direct view of positioning — not inferred from price action or survey sentiment,
but taken from the exchange's own account data.

The question I test here is narrow. When that ratio reaches an extreme — when a large
majority of retail accounts sit on one side — does price subsequently move against them?
And if it does, does it do so always, or only under particular conditions?

The reason to expect anything at all is mechanical rather than psychological. Positions in
perpetual futures are leveraged. A crowd sitting long is a stack of margin and stop levels
below the current price. Those positions are not passive: they have to be closed if price
moves far enough, and closing them means selling. In that sense a crowded book is not just
a signal about what people believe — it is inventory that the market can consume. The
crowd is fuel.

This framing sits close to the predatory-trading literature (Brunnermeier and Pedersen,
2005), where informed participants trade against others whose liquidation is predictable,
and to the crowded-trades literature, where positions concentrated on one side unwind
violently. What those papers usually lack, for equities, is data on who is actually
positioned where. Crypto perpetuals supply exactly that.

## 2. Data

Everything comes from Binance USDT-M perpetual futures, all of it public.

| Series | Source | Range |
|---|---|---|
| Hourly OHLCV | REST API (`/fapi/v1/klines`) | BTC 2019-09, ETH 2019-11 |
| Funding rate (8h) | REST API (`/fapi/v1/fundingRate`) | same |
| Open interest, long/short account ratio, taker ratio (5-min) | `data.binance.vision` daily archive | BTC 2020-09, ETH 2021-12 |
| Liquidations (event level) | CryptoHFTData | 2025-06 onward |

The binding constraint is the metrics archive: the long/short ratio only exists from
September 2020 for BTC and December 2021 for ETH, so the panel starts there. After merging
to an hourly grid the samples are 43,592 hours for BTC and 32,660 for ETH.

Liquidations are the weak link. Binance's own bulk archive for USDT-M liquidation
snapshots is empty, and the only free event-level source I found reaches back about a year.
That is enough to check the mechanism, not enough to make it part of the main result.

## 3. Measuring the crowd

Positioning is taken from `count_long_short_ratio` — the ratio of accounts long to accounts
short. I use the account-based ratio rather than the volume-weighted one deliberately: it
counts people, not size, which is closer to the thing being tested. A handful of large
accounts should not be able to move this measure.

The raw ratio is not comparable across time. Its level drifts, and its variance changes as
the market's character changes. So the working variable is a z-score:

```
z_t = mean over w in {168, 336, 720} of  (x_t - mean_w(x)) / std_w(x)
```

Three lookbacks — one week, two weeks, one month, in hours — averaged. Using a single fixed
window makes the measure hostage to whatever pace the market happens to be running at; a
week-long window that works in a fast market reads a slow one as permanently neutral.
Averaging across lookbacks costs some sharpness and buys stability. An extreme is defined
as |z| > 1.5, which on this sample flags roughly 10% of hours in each direction.

## 4. Method

For an extreme at time *t*, the forward return over *h* hours is the cumulative log return
from *t+1* to *t+h*. There is no overlap between the signal and the return window.

The statistic of interest is the difference between what follows a short extreme and what
follows a long extreme:

```
spread(h) = E[r_{t+1..t+h} | z < -1.5]  -  E[r_{t+1..t+h} | z > +1.5]
```

A positive spread means price moved against the crowd in both directions: down after they
crowded long, up after they crowded short. Significance is from a Welch t-test on the two
groups, and because I look at several horizons I apply Benjamini-Hochberg across them
rather than reading each p-value on its own. Forward windows overlap, so the t-statistics
are optimistic in absolute terms; I treat them as ranking evidence, not as exact.

The second cut conditions on open interest. I take the 30-day growth rate of OI, rank it
into terciles, and compute the spread within each. The idea is to separate two situations
that look identical if you only watch the ratio: a crowd building leveraged positions into
a market that is otherwise quiet, versus a crowd leaning the same way as a large spot bid.
The first is fuel. The second is not.

## 5. Results

### BTC

| horizon | spread | t | n | survives FDR |
|---|---|---|---|---|
| 12h | +0.57% | 11.3 | 9,247 | yes |
| 24h | +0.95% | 13.4 | 9,247 | yes |
| 72h | +1.54% | 13.4 | 9,245 | yes |
| 168h | +1.97% | 10.9 | 9,245 | yes |

The sign is the same at every horizon and the magnitude grows with it. Price does not snap
back immediately after positioning gets extreme — the separation builds over days, which is
what you would expect if the mechanism is positions being worked out of rather than a
sentiment reading being corrected.

### ETH

| horizon | spread | t | n | survives FDR |
|---|---|---|---|---|
| 12h | +0.23% | 3.9 | 6,617 | yes |
| 24h | +0.48% | 5.7 | 6,617 | yes |
| 72h | +0.24% | 1.6 | 6,617 | no |
| 168h | −0.17% | −0.8 | 6,560 | no |

ETH shows the effect at short horizons and then loses it. Taken at face value the two
assets disagree.

### Conditioning on open interest

They stop disagreeing once you split by whether open interest is growing (72h horizon):

| OI regime | BTC spread | t | ETH spread | t |
|---|---|---|---|---|
| flat / falling | +0.28% | 1.2 | −0.07% | −0.3 |
| rising | +1.69% | 8.9 | −1.12% | −5.2 |
| surging | +2.45% | 14.1 | +1.68% | 6.1 |

Two things stand out.

First, on BTC the effect is essentially absent when OI is flat (+0.28%, t = 1.2) and
strongest when OI is surging (+2.45%, t = 14.1). Crowding without leverage accumulating
behind it does very little. That is a direct point in favour of the mechanical reading: it
is not the crowd's opinion that matters, it is the size of the position they have taken on
borrowed money.

Second, ETH's apparent disagreement is a composition effect. In the surging-OI bucket ETH
behaves like BTC (+1.68%, t = 6.1). Its negative unconditional number comes from the
middle bucket, where the spread is −1.12% — crowded longs are followed by *more* upside,
not less. That is the signature of a market where price is being pushed by flow the crowd
happens to be aligned with rather than by the crowd itself. ETH spent much of 2025-26 in
exactly that state.

So the honest summary is not "price reverses against the crowd." It is: price reverses
against the crowd when the crowd is the marginal buyer, and doesn't when it isn't.

### Liquidations

If the mechanism is real, an extreme in long positioning should be followed by more longs
being liquidated. Over the year of liquidation data available:

- BTC: long liquidations in the 24h after a long extreme average $25.0M, versus $10.4M
  otherwise — a factor of 2.4.
- ETH: $15.1M versus $12.4M, a factor of 1.2.

The BTC number is the one worth taking seriously; the ETH ratio is weak and the window is
short. Still, the direction is right, and it is an independent check: nothing in the
liquidation data feeds the positioning measure.

## 6. What this does not show

The account ratio is a proxy. It counts accounts on Binance, not positions across the
market, and it says nothing about the size behind each account. If the composition of who
trades on Binance changed over the sample — and between 2020 and 2026 it certainly did —
part of what I attribute to regime could be attributable to that.

The OI terciles are a coarse instrument. They were chosen because three buckets is the
smallest split that separates "no leverage building" from "a lot of leverage building"
while leaving enough observations in each; nothing about the boundaries is principled.
I read the regime split as a conditional relationship, not as evidence of causation.

Overlapping forward windows inflate the t-statistics. The effect is large enough on BTC
that this is unlikely to be the whole story, but the exact numbers should not be read as
precise.

And this is a study of an effect, not of a strategy. I have not tested whether any of it
survives execution.

## 7. Reproducing

```
pip install -r requirements.txt
python src/build.py       # merge raw dumps into the hourly panel
python src/analysis.py    # spreads by horizon, by OI regime, liquidation check
python src/figures.py
```

The raw Binance dumps are not in the repository — they are large and they are not mine to
host. `data/DATA_NOTES.txt` says exactly which endpoint or archive path each file comes
from.

## References

Brunnermeier, M. and Pedersen, L. (2005). Predatory Trading. *Journal of Finance* 60(4).

Brunnermeier, M. and Pedersen, L. (2009). Market Liquidity and Funding Liquidity.
*Review of Financial Studies* 22(6).

Ho, T. and Stoll, H. (1981). Optimal Dealer Pricing under Transactions and Return
Uncertainty. *Journal of Financial Economics* 9(1).

Benjamini, Y. and Hochberg, Y. (1995). Controlling the False Discovery Rate.
*Journal of the Royal Statistical Society B* 57(1).
