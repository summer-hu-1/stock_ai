from typing import Dict, Any, Optional, List
import pandas as pd
from .breakout_signal import BreakoutSignal
from .trend_signal import TrendSignal
from .reversal_signal import ReversalSignal
from .volume_signal import VolumeSignal


class SignalEngine:
    def __init__(self):
        self.signals = {
            "breakout": BreakoutSignal(),
            "trend": TrendSignal(),
            "reversal": ReversalSignal(),
            "volume": VolumeSignal(),
        }

    def generate(self, df: pd.DataFrame, factors: Dict[str, Any] = None, include_signals: List[str] = None) -> Dict[str, Any]:
        if df is None or len(df) == 0:
            return self._empty_result()

        if include_signals is None:
            include_signals = list(self.signals.keys())

        result = {}
        for signal_name in include_signals:
            if signal_name in self.signals:
                signal = self.signals[signal_name]
                try:
                    result[signal_name] = signal.generate(df, factors)
                except Exception as e:
                    result[signal_name] = {"error": str(e), "signal": "error"}

        result["summary"] = self._generate_summary(result)

        return result

    def generate_single(self, df: pd.DataFrame, signal_name: str, factors: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        if signal_name not in self.signals:
            return None

        try:
            return self.signals[signal_name].generate(df, factors)
        except Exception:
            return None

    def get_signal_names(self) -> List[str]:
        return list(self.signals.keys())

    def _generate_summary(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        summary = {
            "overall_direction": "neutral",
            "overall_strength": 50,
            "bullish_signals": [],
            "bearish_signals": [],
            "neutral_signals": [],
            "signal_count": 0,
        }

        for name, data in signals.items():
            if name == "summary" or name == "error":
                continue

            if "direction" not in data:
                continue

            summary["signal_count"] += 1
            signal_type = data.get("signal", "unknown")
            strength = data.get("strength", 50)

            if data["direction"] == "bullish" and strength >= 55:
                summary["bullish_signals"].append({
                    "type": name,
                    "signal": signal_type,
                    "strength": strength
                })
            elif data["direction"] == "bearish" and strength >= 55:
                summary["bearish_signals"].append({
                    "type": name,
                    "signal": signal_type,
                    "strength": strength
                })
            else:
                summary["neutral_signals"].append({
                    "type": name,
                    "signal": signal_type,
                    "strength": strength
                })

        bullish_count = len(summary["bullish_signals"])
        bearish_count = len(summary["bearish_signals"])

        if bullish_count > bearish_count:
            summary["overall_direction"] = "bullish"
            summary["overall_strength"] = min(95, 50 + (bullish_count - bearish_count) * 15)
        elif bearish_count > bullish_count:
            summary["overall_direction"] = "bearish"
            summary["overall_strength"] = min(95, 50 + (bearish_count - bullish_count) * 15)
        else:
            summary["overall_direction"] = "neutral"
            summary["overall_strength"] = 50

        return summary

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "breakout": {},
            "trend": {},
            "reversal": {},
            "volume": {},
            "summary": {
                "overall_direction": "neutral",
                "overall_strength": 50,
                "bullish_signals": [],
                "bearish_signals": [],
                "neutral_signals": [],
                "signal_count": 0,
            }
        }


def generate_signals(df: pd.DataFrame, factors: Dict[str, Any] = None) -> Dict[str, Any]:
    engine = SignalEngine()
    return engine.generate(df, factors)


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from factors.factor_engine import FactorEngine

    import pandas as pd
    import numpy as np

    dates = pd.date_range('2024-01-01', periods=100)
    df = pd.DataFrame({
        'date': dates,
        'open': np.random.uniform(10, 20, 100),
        'high': np.random.uniform(12, 22, 100),
        'low': np.random.uniform(8, 18, 100),
        'close': np.random.uniform(10, 20, 100),
        'volume': np.random.uniform(1000000, 5000000, 100),
    })

    factor_engine = FactorEngine()
    factors = factor_engine.calculate(df)

    signal_engine = SignalEngine()
    signals = signal_engine.generate(df, factors)

    print("=" * 50)
    print("信号系统测试")
    print("=" * 50)

    for name, data in signals.items():
        if name == "summary":
            print(f"\n【综合信号】")
            print(f"  方向: {data['overall_direction']}")
            print(f"  强度: {data['overall_strength']}")
            print(f"  看多信号数: {len(data['bullish_signals'])}")
            print(f"  看空信号数: {len(data['bearish_signals'])}")
        else:
            print(f"\n【{name.upper()}信号】")
            print(f"  信号类型: {data.get('signal', 'N/A')}")
            print(f"  方向: {data.get('direction', 'N/A')}")
            print(f"  强度: {data.get('strength', 0)}")
