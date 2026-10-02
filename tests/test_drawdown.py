import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from bist_drawdown_census import detect_drawdowns, apply_rules


def synthetic_prices():
    dates = pd.date_range("2020-01-01", periods=8, freq="D")
    close = [100, 105, 100, 94, 88, 92, 100, 106]
    high = [x + 1 for x in close]
    low = [x - 1 for x in close]
    return pd.DataFrame({
        "Date": dates,
        "Open": close,
        "High": high,
        "Low": low,
        "Close": close,
        "Volume": [1] * len(close),
    })


def test_detects_single_drawdown():
    prices = synthetic_prices()
    episodes = detect_drawdowns(prices, 0.10)
    assert len(episodes) == 1
    row = episodes.iloc[0]
    assert row["peak_close"] == 105
    assert row["trough_close"] == 88
    assert row["max_drawdown"] < -0.10


def test_observable_minus_10_entry_fills():
    prices = synthetic_prices()
    episodes = apply_rules(prices, detect_drawdowns(prices, 0.10))
    row = episodes.iloc[0]
    assert pd.notna(row["d10_fill_date"])
    assert row["d10_level"] == 94.5
    assert row["staged_capital_deployed"] >= 0.25
