# BIST 100 Drawdown & Recovery Research — Brief

## Question
How long has BIST 100 historically taken to recover after observable entries during ≥10% drawdowns, without assuming the investor catches the exact bottom?

## Sample
- 7,794 daily observations
- 21 Mar 1995 – 22 May 2026
- 36 completed ≥10% drawdown episodes
- 1 open episode at the end of the series

## Core nominal result

| Rule | Median recovery |
|---|---:|
| -10% entry | 46.5 days |
| -15% entry | 29.5 days |
| -20% entry | 37.5 days |
| Staged 25/35/40 | **21.5 days** |

## Severity result

| Maximum drawdown | Median staged recovery |
|---|---:|
| 10–15% | 6 days |
| 15–20% | 8 days |
| 20–30% | 24 days |
| 30%+ | 235 days |

The severity split is more informative than the pooled mean.

## Real recovery
At a 10 bps-per-side cost assumption:
- staged: 21.5 nominal → **30 real days**
- -10%: 46.5 nominal → **74 real days**

## Interpretation
The evidence does not imply that every drawdown should be bought. It shows that moderate corrections and structural bear markets have very different historical recovery distributions, and that a staged cost basis can shorten nominal breakeven time while using less capital in shallower drawdowns.

## Limitation
The backtest uses the BIST 100 price index. Reinvested dividends, taxes, market impact and intraday order sequencing are outside the model.
