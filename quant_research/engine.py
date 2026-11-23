"""Long-only moving-average research with next-open execution and explicit costs.

An indicator formed using close[t-1] is tradable no earlier than open[t].
Positions held from open[t] to open[t+1] use open-to-open returns.
No network, model, order-routing, or account access is performed here.
"""

from dataclasses import dataclass
import math

import pandas as pd

REQUIRED = ("date", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class Costs:
    commission_bps: float = 3.0
    slippage_bps: float = 3.0
    sell_tax_bps: float = 0.0  # ETF example; A-share stock taxes differ.

    def __post_init__(self):
        for value in (self.commission_bps, self.slippage_bps, self.sell_tax_bps):
            if not math.isfinite(value) or not 0 <= value <= 1000:
                raise ValueError("Costs must be finite and between 0 and 1000 bps")


def validate_bars(bars: pd.DataFrame) -> pd.DataFrame:
    """Return an ascending, strictly validated copy of daily OHLCV bars."""
    absent = [k for k in REQUIRED if k not in bars.columns]
    if absent:
        raise ValueError(f"Missing columns: {', '.join(absent)}")
    if len(bars) < 3:
        raise ValueError("At least three bars are required")
    x = bars.loc[:, REQUIRED].copy()
    x["date"] = pd.to_datetime(x["date"], errors="raise")
    if x["date"].isna().any() or x["date"].duplicated().any():
        raise ValueError("Dates must be non-null and unique")
    x = x.sort_values("date").reset_index(drop=True)
    for key in REQUIRED[1:]:
        x[key] = pd.to_numeric(x[key], errors="raise")
        if not x[key].map(math.isfinite).all():
            raise ValueError(f"Non-finite {key}")
    if (x[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError("Prices must be positive")
    if (x["volume"] < 0).any():
        raise ValueError("Volume must be non-negative")
    if (x["low"] > x[["open", "close", "high"]].min(axis=1)).any() or (
        x["high"] < x[["open", "close", "low"]].max(axis=1)
    ).any():
        raise ValueError("Inconsistent OHLC values")
    return x


def backtest_ma(bars: pd.DataFrame, fast: int = 5, slow: int = 20,
                costs: Costs = Costs(), annual_days: int = 252) -> tuple[pd.DataFrame, dict]:
    """Research MA(fast)>MA(slow); execute at next open, no lookahead.

    Results cover open[t] -> open[t+1]. The final open is used to value and
    liquidate the last position. Fees are proportional approximations, not
    broker-specific min commissions, bid/ask fills, suspensions, or limit rules.
    """
    if not isinstance(fast, int) or not isinstance(slow, int) or not 1 <= fast < slow:
        raise ValueError("Require integers 1 <= fast < slow")
    if annual_days < 1:
        raise ValueError("annual_days must be positive")
    x = validate_bars(bars)
    if len(x) < slow + 2:
        raise ValueError(f"Need at least {slow + 2} bars")

    ma_fast = x["close"].rolling(fast).mean()
    ma_slow = x["close"].rolling(slow).mean()
    # t-1 close is observable before t open; t close is NOT.
    positions = (ma_fast.shift(1) > ma_slow.shift(1)).fillna(False).astype(int)
    begin = slow
    end_exclusive = len(x) - 1
    result = pd.DataFrame({
        "date": x["date"].iloc[begin:end_exclusive].to_numpy(),
        "signal_date": x["date"].iloc[begin-1:end_exclusive-1].to_numpy(),
        "position": positions.iloc[begin:end_exclusive].to_numpy(),
        "entry_open": x["open"].iloc[begin:end_exclusive].to_numpy(),
        "next_open": x["open"].iloc[begin+1:].to_numpy(),
    })
    result["gross_return"] = result["position"] * (
        result["next_open"] / result["entry_open"] - 1.0
    )
    previous_position = result["position"].shift(1).fillna(0).astype(int)
    delta = result["position"] - previous_position
    buy = delta.clip(lower=0)
    sell = (-delta).clip(lower=0)
    fee = (costs.commission_bps + costs.slippage_bps) / 10000.0
    result["cost_return"] = (buy + sell) * fee + sell * costs.sell_tax_bps / 10000.0
    # Mandatory liquidation at final available next-open mark.
    if int(result["position"].iloc[-1]) == 1:
        result.loc[result.index[-1], "cost_return"] += fee + costs.sell_tax_bps / 10000.0
    result["net_return"] = result["gross_return"] - result["cost_return"]
    result["equity"] = (1.0 + result["net_return"]).cumprod()
    result["benchmark_equity"] = (
        result["next_open"] / result["entry_open"].iloc[0]
    )  # pre-cost buy-and-hold comparison

    equity = result["equity"]
    drawdown = equity / equity.cummax().clip(lower=1.0) - 1.0
    volatility = result["net_return"].std(ddof=1)
    sharpe = (result["net_return"].mean() / volatility * math.sqrt(annual_days)
              if pd.notna(volatility) and volatility > 0 else None)
    summary = {
        "total_return": float(equity.iloc[-1] - 1.0),
        "benchmark_return_pre_cost": float(result["benchmark_equity"].iloc[-1] - 1.0),
        "max_drawdown": float(drawdown.min()),
        "annualized_sharpe_rf0": float(sharpe) if sharpe is not None else None,
        "entries": int((delta > 0).sum()),
        "exits_including_liquidation": int((delta < 0).sum()) + int(result["position"].iloc[-1]),
        "exposure": float(result["position"].mean()),
        "observations": int(len(result)),
        "commission_bps": costs.commission_bps,
        "slippage_bps": costs.slippage_bps,
        "sell_tax_bps": costs.sell_tax_bps,
    }
    return result, summary
