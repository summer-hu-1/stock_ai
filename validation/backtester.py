from typing import Dict, Any, List, Optional, Callable
import pandas as pd
import numpy as np
from datetime import datetime


class TradeRecord:
    def __init__(self):
        self.trades = []

    def add_trade(
        self,
        date: datetime,
        action: str,
        price: float,
        shares: int,
        code: str = "unknown",
        signal_type: str = "",
        reason: str = ""
    ):
        self.trades.append({
            "date": date,
            "action": action,
            "price": price,
            "shares": shares,
            "code": code,
            "signal_type": signal_type,
            "reason": reason,
            "pnl": 0.0,
            "hold_days": 0
        })

    def update_pnl(self, index: int, exit_price: float, hold_days: int):
        if index < len(self.trades):
            trade = self.trades[index]
            trade["exit_price"] = exit_price
            trade["pnl"] = (exit_price - trade["price"]) * trade["shares"]
            trade["hold_days"] = hold_days
            trade["pnl_pct"] = ((exit_price - trade["price"]) / trade["price"]) * 100

    def get_summary(self) -> Dict[str, Any]:
        if not self.trades:
            return {"total_trades": 0}

        trades = pd.DataFrame(self.trades)
        profitable = trades[trades["pnl"] > 0]
        losing = trades[trades["pnl"] <= 0]

        return {
            "total_trades": len(self.trades),
            "winning_trades": len(profitable),
            "losing_trades": len(losing),
            "win_rate": len(profitable) / len(self.trades) * 100,
            "avg_pnl": trades["pnl"].mean(),
            "avg_pnl_pct": trades["pnl_pct"].mean(),
            "max_win": trades["pnl"].max(),
            "max_loss": trades["pnl"].min(),
            "total_pnl": trades["pnl"].sum(),
            "avg_hold_days": trades["hold_days"].mean(),
            "best_trade": trades.iloc[trades["pnl"].idxmax()].to_dict() if len(trades) > 0 else None,
            "worst_trade": trades.iloc[trades["pnl"].idxmin()].to_dict() if len(trades) > 0 else None,
        }


class Backtester:
    def __init__(
        self,
        initial_capital: float = 100000.0,
        position_size: float = 0.1,
        stop_loss_pct: float = 5.0,
        take_profit_pct: float = 10.0,
        max_hold_days: int = 10
    ):
        self.initial_capital = initial_capital
        self.position_size = position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_hold_days = max_hold_days

        self.reset()

    def reset(self):
        self.capital = self.initial_capital
        self.portfolio = {}
        self.open_positions = []
        self.trade_record = TradeRecord()
        self.daily_equity = []
        self.current_date = None

    def get_position_value(self, code: str) -> float:
        if code in self.portfolio:
            pos = self.portfolio[code]
            return pos["shares"] * pos["avg_cost"]
        return 0.0

    def get_total_equity(self) -> float:
        portfolio_value = sum(
            pos["shares"] * pos["avg_cost"] for pos in self.portfolio.values()
        )
        return self.capital + portfolio_value

    def enter_position(
        self,
        date: datetime,
        code: str,
        price: float,
        signal_type: str = "",
        reason: str = ""
    ):
        if code in self.portfolio:
            return

        max_investment = self.get_total_equity() * self.position_size
        shares = int(max_investment / price)

        if shares <= 0:
            return

        self.capital -= shares * price
        self.portfolio[code] = {
            "shares": shares,
            "avg_cost": price,
            "entry_date": date,
            "signal_type": signal_type,
            "stop_loss": price * (1 - self.stop_loss_pct / 100),
            "take_profit": price * (1 + self.take_profit_pct / 100),
            "trade_index": len(self.trade_record.trades)
        }

        self.trade_record.add_trade(
            date=date,
            action="BUY",
            price=price,
            shares=shares,
            code=code,
            signal_type=signal_type,
            reason=reason
        )

    def exit_position(self, date: datetime, code: str, price: float, reason: str = ""):
        if code not in self.portfolio:
            return

        pos = self.portfolio[code]
        pnl = (price - pos["avg_cost"]) * pos["shares"]
        hold_days = (date - pos["entry_date"]).days

        self.capital += pos["shares"] * price

        trade_index = pos["trade_index"]
        self.trade_record.update_pnl(trade_index, price, hold_days)

        del self.portfolio[code]

    def process_bar(self, date: datetime, code: str, ohlcv: Dict[str, float]):
        self.current_date = date

        for pos_code in list(self.portfolio.keys()):
            pos = self.portfolio[pos_code]
            hold_days = (date - pos["entry_date"]).days

            if hold_days >= self.max_hold_days:
                self.exit_position(date, pos_code, ohlcv["close"], reason="持有到期")
                continue

            if ohlcv["low"] <= pos["stop_loss"]:
                self.exit_position(date, pos_code, pos["stop_loss"], reason="止损")
                continue

            if ohlcv["high"] >= pos["take_profit"]:
                self.exit_position(date, pos_code, pos["take_profit"], reason="止盈")
                continue

        self.daily_equity.append({
            "date": date,
            "equity": self.get_total_equity()
        })

    def run(
        self,
        df: pd.DataFrame,
        signal_generator: Callable[[pd.DataFrame, int], Optional[Dict[str, Any]]],
        code: str = "TEST"
    ) -> Dict[str, Any]:
        self.reset()

        for i in range(len(df)):
            row = df.iloc[i]
            date = pd.to_datetime(row["date"])

            signal = signal_generator(df, i)

            if signal and signal.get("direction") == "bullish":
                self.enter_position(
                    date=date,
                    code=code,
                    price=float(row["open"]),
                    signal_type=signal.get("signal", ""),
                    reason=signal.get("reason", "")
                )

            self.process_bar(date, code, {
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"])
            })

        equity_df = pd.DataFrame(self.daily_equity)
        if not equity_df.empty:
            equity_df["return"] = equity_df["equity"].pct_change()
            equity_df["cum_return"] = (1 + equity_df["return"]).cumprod()

            total_return = (equity_df["equity"].iloc[-1] / self.initial_capital - 1) * 100
            max_drawdown = self._calc_max_drawdown(equity_df["cum_return"])
            sharpe_ratio = self._calc_sharpe_ratio(equity_df["return"])
        else:
            total_return = 0
            max_drawdown = 0
            sharpe_ratio = 0

        summary = self.trade_record.get_summary()
        summary.update({
            "initial_capital": self.initial_capital,
            "final_equity": self.get_total_equity(),
            "total_return": total_return,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "equity_curve": equity_df.to_dict("records") if not equity_df.empty else []
        })

        return summary

    def _calc_max_drawdown(self, returns: pd.Series) -> float:
        peak = returns.cummax()
        drawdown = (returns - peak) / peak
        return -drawdown.min() * 100

    def _calc_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        if returns.empty:
            return 0.0
        excess_returns = returns - risk_free_rate / 252
        return excess_returns.mean() / excess_returns.std() * np.sqrt(252)
