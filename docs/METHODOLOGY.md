# Methodology Notes

## Research design

The project has two layers:

1. **Descriptive midpoint benchmark**  
   \(M_{50}=(X+Y)/2\), where \(Y\) is the realized trough. This is useful for describing historical midpoint recovery but is not tradable ex ante.

2. **Observable trigger backtest**  
   -10%, -15%, -20% peak-relative limits and a 25%/35%/40% staged rule.

The final conclusions rely primarily on the second layer.

## Episode detection

An episode begins at a high-water-mark close. It ends when the same peak is recovered. The episode trough is the minimum close before recovery. Episodes below 10% maximum drawdown are excluded.

## Fill model

A limit is filled when daily low <= limit level.

No intraday sequencing is modeled. Therefore, if a daily bar touches several limits, all qualifying limits are treated as filled.

## Recovery definition

Primary recovery:
first closing price at/above cost after the episode trough.

This is deliberately stricter than “first profitable close after entry.”

## Inflation

Monthly CPI is mapped to each daily observation's calendar month.

Single-entry real breakeven compares:
- inflation-adjusted liquidation proceeds, and
- inflation-adjusted entry cash outflow.

Staged real breakeven sums the real outflow of each tranche separately.

## Transaction costs

A symmetric fee \(f\) is applied:
- purchase cost = price x (1+f)
- liquidation proceeds = price x (1-f)

Sensitivity:
0 / 5 / 10 / 25 basis points per side.

## Why medians matter

Recovery-time distributions are highly right-skewed. Structural episodes such as 2000–2001 and 2007–2008 create multi-year tails, making the arithmetic mean much larger than the experience of a typical episode.

The project therefore reports:
- mean
- median
- recovery-horizon frequencies
- severity buckets
- unresolved real recoveries

## Statistical test

For the paired staged-vs.-10% comparison:
- 28 staged-faster episodes
- 8 ties
- 0 staged-slower episodes

The sign test is computed only on non-tied pairs.

This tests direction of recovery-time differences, not investment-return superiority.

## Remaining extensions

- official Borsa İstanbul total-return series;
- broker-specific commissions and taxes;
- risk-free return on idle staged capital;
- regime-conditioned models;
- bootstrap confidence intervals for severity buckets;
- international benchmark comparison.
