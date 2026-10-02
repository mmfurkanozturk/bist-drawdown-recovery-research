# LinkedIn post draft

I started with a simple question:

**When BIST falls sharply, what happens if you accumulate during the decline instead of trying to catch the exact bottom?**

I built a mechanical BIST 100 drawdown census using 7,794 daily observations from 1995 to May 2026.

Rather than selecting famous crises first, I detected every completed drawdown of at least 10% directly from the price series and then tested observable entries at -10%, -15%, -20%, plus a staged 25% / 35% / 40% approach.

A few results stood out:

- staged median nominal recovery: **21.5 days**
- staged median inflation-adjusted recovery: **30 days**
- median staged recovery for 10–15% drawdowns: **6 days**
- median staged recovery for 20–30% drawdowns: **24 days**
- median staged recovery for 30%+ drawdowns: **235 days**

The main takeaway was not “buy every crash.”

It was that **ordinary corrections and structural crises are statistically very different regimes**. Once the drawdown moves beyond roughly 30%, recovery time and downside risk change dramatically.

I also tested inflation adjustment and transaction-cost sensitivity. In this framework, inflation changed the recovery picture much more than modest transaction-cost assumptions.

The project includes the full drawdown census, methodology, reproducible Python code, robustness analysis, and Excel results.

#QuantitativeFinance #BIST100 #Python #RiskManagement #DataAnalysis #FinancialMarkets
