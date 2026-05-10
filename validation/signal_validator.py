from typing import Dict, Any, List, Callable
import pandas as pd
import numpy as np
from datetime import datetime


class SignalValidator:
    def __init__(self):
        pass

    def validate_signal(
        self,
        df: pd.DataFrame,
        signal_column: str = "signal",
        direction_column: str = "direction",
        lookahead_days: int = 5
    ) -> Dict[str, Any]:
        signals = df.dropna(subset=[signal_column])
        
        if len(signals) == 0:
            return {"error": "No signals found"}

        results = []
        bullish_signals = signals[signals[direction_column] == "bullish"]
        bearish_signals = signals[signals[direction_column] == "bearish"]

        for _, row in signals.iterrows():
            signal_date = pd.to_datetime(row["date"])
            idx = df[df["date"] == row["date"]].index[0]
            
            if idx + lookahead_days >= len(df):
                continue

            future_df = df.iloc[idx:idx + lookahead_days + 1]
            entry_price = float(future_df.iloc[0]["open"])
            max_high = float(future_df["high"].max())
            min_low = float(future_df["low"].min())
            final_close = float(future_df.iloc[-1]["close"])

            profit_target = entry_price * 1.05
            stop_loss = entry_price * 0.95

            hit_profit = max_high >= profit_target
            hit_stop = min_low <= stop_loss

            if hit_profit and hit_stop:
                outcome = "both"
            elif hit_profit:
                outcome = "win"
            elif hit_stop:
                outcome = "loss"
            else:
                outcome = "hold"

            results.append({
                "date": signal_date,
                "signal": row[signal_column],
                "direction": row[direction_column],
                "entry_price": entry_price,
                "max_high": max_high,
                "min_low": min_low,
                "final_close": final_close,
                "return_pct": (final_close - entry_price) / entry_price * 100,
                "hit_profit": hit_profit,
                "hit_stop": hit_stop,
                "outcome": outcome
            })

        if not results:
            return {"error": "No valid signals to validate"}

        results_df = pd.DataFrame(results)

        bullish_results = results_df[results_df["direction"] == "bullish"]
        bearish_results = results_df[results_df["direction"] == "bearish"]

        return {
            "total_signals": len(results_df),
            "bullish_signals": len(bullish_results),
            "bearish_signals": len(bearish_results),
            "bullish_win_rate": self._calc_win_rate(bullish_results),
            "bearish_win_rate": self._calc_win_rate(bearish_results),
            "bullish_avg_return": bullish_results["return_pct"].mean(),
            "bearish_avg_return": bearish_results["return_pct"].mean(),
            "overall_win_rate": self._calc_win_rate(results_df),
            "overall_avg_return": results_df["return_pct"].mean(),
            "max_win_return": results_df["return_pct"].max(),
            "max_loss_return": results_df["return_pct"].min(),
            "signal_distribution": results_df[signal_column].value_counts().to_dict(),
            "outcome_distribution": results_df["outcome"].value_counts().to_dict(),
            "results": results
        }

    def _calc_win_rate(self, df: pd.DataFrame) -> float:
        if len(df) == 0:
            return 0.0
        wins = df[(df["outcome"] == "win") | ((df["outcome"] == "both") & (df["return_pct"] > 0))]
        return len(wins) / len(df) * 100

    def validate_signals_across_multiple_stocks(
        self,
        stock_data_list: List[Dict[str, Any]],
        lookahead_days: int = 5
    ) -> Dict[str, Any]:
        all_results = []
        
        for stock in stock_data_list:
            df = stock.get("df")
            if df is None or len(df) == 0:
                continue

            signals = stock.get("signals", {})
            if not signals or "summary" not in signals:
                continue

            df_with_signals = df.copy()
            df_with_signals["signal"] = ""
            df_with_signals["direction"] = "neutral"

            for i in range(len(df)):
                date = df.iloc[i]["date"]
                daily_signals = self._extract_daily_signals(signals, i)
                
                if daily_signals:
                    df_with_signals.loc[i, "signal"] = "; ".join([s.get("signal", "") for s in daily_signals])
                    directions = [s.get("direction", "neutral") for s in daily_signals]
                    if "bullish" in directions and "bearish" not in directions:
                        df_with_signals.loc[i, "direction"] = "bullish"
                    elif "bearish" in directions and "bullish" not in directions:
                        df_with_signals.loc[i, "direction"] = "bearish"

            result = self.validate_signal(df_with_signals, lookahead_days=lookahead_days)
            if "error" not in result:
                result["code"] = stock.get("code", "unknown")
                result["name"] = stock.get("name", "unknown")
                all_results.append(result)

        if not all_results:
            return {"error": "No valid results"}

        return {
            "total_stocks": len(all_results),
            "avg_win_rate": np.mean([r["overall_win_rate"] for r in all_results]),
            "avg_return": np.mean([r["overall_avg_return"] for r in all_results]),
            "best_stock": max(all_results, key=lambda x: x["overall_win_rate"]),
            "worst_stock": min(all_results, key=lambda x: x["overall_win_rate"]),
            "detailed_results": all_results
        }

    def _extract_daily_signals(self, signals: Dict[str, Any], day_index: int) -> List[Dict[str, Any]]:
        daily_signals = []
        for signal_type, signal_data in signals.items():
            if signal_type == "summary":
                continue
            if isinstance(signal_data, dict) and "signal" in signal_data:
                daily_signals.append(signal_data)
        return daily_signals
