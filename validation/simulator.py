from typing import Dict, Any, List, Optional, Callable
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import deque


class Position:
    def __init__(self, code: str, entry_price: float, shares: int, entry_date: datetime):
        self.code = code
        self.entry_price = entry_price
        self.shares = shares
        self.entry_date = entry_date
        self.current_price = entry_price
        self.pnl = 0.0
        self.pnl_pct = 0.0

    def update(self, price: float):
        self.current_price = price
        self.pnl = (price - self.entry_price) * self.shares
        self.pnl_pct = ((price - self.entry_price) / self.entry_price) * 100

    def get_value(self) -> float:
        return self.shares * self.current_price


class Portfolio:
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}
        self.history = []

    def get_total_equity(self) -> float:
        positions_value = sum(pos.get_value() for pos in self.positions.values())
        return self.cash + positions_value

    def buy(self, code: str, price: float, shares: int, date: datetime) -> bool:
        cost = price * shares
        if cost > self.cash:
            return False

        self.cash -= cost
        
        if code in self.positions:
            pos = self.positions[code]
            total_shares = pos.shares + shares
            self.positions[code] = Position(
                code,
                (pos.entry_price * pos.shares + price * shares) / total_shares,
                total_shares,
                pos.entry_date
            )
        else:
            self.positions[code] = Position(code, price, shares, date)

        self._record(date)
        return True

    def sell(self, code: str, price: float, shares: int, date: datetime) -> bool:
        if code not in self.positions or self.positions[code].shares < shares:
            return False

        pos = self.positions[code]
        self.cash += price * shares
        pos.shares -= shares

        if pos.shares == 0:
            del self.positions[code]

        self._record(date)
        return True

    def close_position(self, code: str, price: float, date: datetime) -> bool:
        if code not in self.positions:
            return False

        pos = self.positions[code]
        self.cash += price * pos.shares
        del self.positions[code]

        self._record(date)
        return True

    def update_positions(self, prices: Dict[str, float], date: datetime):
        for code, pos in self.positions.items():
            if code in prices:
                pos.update(prices[code])

        self._record(date)

    def _record(self, date: datetime):
        self.history.append({
            "date": date,
            "cash": self.cash,
            "equity": self.get_total_equity(),
            "positions": {
                code: {
                    "shares": pos.shares,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "pnl": pos.pnl,
                    "pnl_pct": pos.pnl_pct
                } for code, pos in self.positions.items()
            }
        })

    def get_summary(self) -> Dict[str, Any]:
        if not self.history:
            return {}

        history_df = pd.DataFrame(self.history)
        history_df["date"] = pd.to_datetime(history_df["date"])
        history_df["return"] = history_df["equity"].pct_change()
        history_df["cum_return"] = (1 + history_df["return"]).cumprod()

        final_equity = history_df["equity"].iloc[-1]
        total_return = ((final_equity / self.initial_capital) - 1) * 100

        peak = history_df["cum_return"].cummax()
        drawdown = (history_df["cum_return"] - peak) / peak
        max_drawdown = -drawdown.min() * 100

        returns = history_df["return"].dropna()
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0

        return {
            "initial_capital": self.initial_capital,
            "final_equity": final_equity,
            "total_return": total_return,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "max_equity": history_df["equity"].max(),
            "min_equity": history_df["equity"].min(),
            "avg_daily_return": returns.mean() * 100,
            "volatility": returns.std() * np.sqrt(252) * 100,
            "history": self.history
        }


class Simulator:
    def __init__(
        self,
        initial_capital: float = 100000.0,
        max_positions: int = 5,
        position_size: float = 0.1,
        stop_loss_pct: float = 5.0,
        take_profit_pct: float = 15.0,
        max_hold_days: int = 15
    ):
        self.portfolio = Portfolio(initial_capital)
        self.max_positions = max_positions
        self.position_size = position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_hold_days = max_hold_days

        self.trade_log = []
        self.signal_log = []

    def _get_max_investment(self) -> float:
        return self.portfolio.get_total_equity() * self.position_size

    def _can_open_new_position(self) -> bool:
        return len(self.portfolio.positions) < self.max_positions

    def process_signal(
        self,
        date: datetime,
        code: str,
        signal: Dict[str, Any],
        price: float
    ):
        self.signal_log.append({
            "date": date,
            "code": code,
            "signal": signal
        })

        if signal.get("direction") == "bullish" and self._can_open_new_position():
            max_investment = self._get_max_investment()
            shares = int(max_investment / price)

            if shares > 0 and self.portfolio.buy(code, price, shares, date):
                self.trade_log.append({
                    "date": date,
                    "action": "BUY",
                    "code": code,
                    "price": price,
                    "shares": shares,
                    "signal_type": signal.get("signal", ""),
                    "reason": signal.get("reason", "")
                })

    def process_price_update(self, date: datetime, prices: Dict[str, float]):
        self.portfolio.update_positions(prices, date)

        for code, pos in list(self.portfolio.positions.items()):
            if code not in prices:
                continue

            current_price = prices[code]
            hold_days = (date - pos.entry_date).days

            if hold_days >= self.max_hold_days:
                self.portfolio.close_position(code, current_price, date)
                self.trade_log.append({
                    "date": date,
                    "action": "SELL",
                    "code": code,
                    "price": current_price,
                    "shares": pos.shares,
                    "reason": "持有到期"
                })
                continue

            pnl_pct = ((current_price - pos.entry_price) / pos.entry_price) * 100

            if pnl_pct <= -self.stop_loss_pct:
                self.portfolio.close_position(code, current_price, date)
                self.trade_log.append({
                    "date": date,
                    "action": "SELL",
                    "code": code,
                    "price": current_price,
                    "shares": pos.shares,
                    "reason": f"止损: {pnl_pct:.1f}%"
                })
                continue

            if pnl_pct >= self.take_profit_pct:
                self.portfolio.close_position(code, current_price, date)
                self.trade_log.append({
                    "date": date,
                    "action": "SELL",
                    "code": code,
                    "price": current_price,
                    "shares": pos.shares,
                    "reason": f"止盈: {pnl_pct:.1f}%"
                })
                continue

    def run(
        self,
        price_data: List[Dict[str, Any]],
        signal_generator: Callable[[datetime], List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        for day_data in price_data:
            date = pd.to_datetime(day_data["date"])
            prices = day_data.get("prices", {})

            signals = signal_generator(date)
            for signal in signals:
                code = signal.get("code")
                price = prices.get(code)
                if code and price:
                    self.process_signal(date, code, signal, price)

            self.process_price_update(date, prices)

        summary = self.portfolio.get_summary()
        summary.update({
            "trade_log": self.trade_log,
            "signal_log": self.signal_log,
            "total_trades": len(self.trade_log),
            "total_signals": len(self.signal_log)
        })

        return summary
