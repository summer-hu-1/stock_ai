from typing import Dict, Any, Optional
import pandas as pd
from .trend_factor import TrendFactor
from .volume_factor import VolumeFactor
from .momentum_factor import MomentumFactor
from .volatility_factor import VolatilityFactor
from .strength_factor import StrengthFactor


class FactorEngine:
    def __init__(self):
        self.factors = {
            "trend": TrendFactor(),
            "volume": VolumeFactor(),
            "momentum": MomentumFactor(),
            "volatility": VolatilityFactor(),
            "strength": StrengthFactor(),
        }

    def calculate(self, df: pd.DataFrame, include_factors: list = None) -> Dict[str, Any]:
        if df is None or len(df) == 0:
            return self._empty_result()

        if include_factors is None:
            include_factors = list(self.factors.keys())

        result = {}
        for factor_name in include_factors:
            if factor_name in self.factors:
                factor = self.factors[factor_name]
                try:
                    result[factor_name] = factor.calculate(df)
                except Exception as e:
                    result[factor_name] = {"error": str(e)}

        result["summary"] = self._generate_summary(result)

        return result

    def calculate_single(self, df: pd.DataFrame, factor_name: str) -> Optional[Dict[str, Any]]:
        if factor_name not in self.factors:
            return None

        try:
            return self.factors[factor_name].calculate(df)
        except Exception:
            return None

    def get_factor_names(self) -> list:
        return list(self.factors.keys())

    def _generate_summary(self, factors: Dict[str, Any]) -> Dict[str, Any]:
        summary = {
            "overall_score": 50,
            "bullish_signals": 0,
            "bearish_signals": 0,
            "neutral_signals": 0,
        }

        if "trend" in factors and "ma_bullish" in factors["trend"]:
            if factors["trend"]["ma_bullish"]:
                summary["bullish_signals"] += 1
            else:
                summary["bearish_signals"] += 1

        if "volume" in factors and "volume_breakout" in factors["volume"]:
            if factors["volume"]["volume_breakout"]:
                summary["bullish_signals"] += 1

        if "momentum" in factors and "return_5d" in factors["momentum"]:
            if factors["momentum"]["return_5d"] > 3:
                summary["bullish_signals"] += 1
            elif factors["momentum"]["return_5d"] < -3:
                summary["bearish_signals"] += 1

        total_signals = summary["bullish_signals"] + summary["bearish_signals"] + summary["neutral_signals"]
        if total_signals > 0:
            summary["overall_score"] = int(
                50 + (summary["bullish_signals"] - summary["bearish_signals"]) * 15
            )
            summary["overall_score"] = max(0, min(100, summary["overall_score"]))

        return summary

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "trend": {},
            "volume": {},
            "momentum": {},
            "volatility": {},
            "strength": {},
            "summary": {
                "overall_score": 50,
                "bullish_signals": 0,
                "bearish_signals": 0,
                "neutral_signals": 0,
            }
        }


def calculate_factors(df: pd.DataFrame) -> Dict[str, Any]:
    engine = FactorEngine()
    return engine.calculate(df)


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from core.datahub import get_datahub

    datahub = get_datahub()
    df = datahub.get_ohlcv_dataframe("000002", "cn")

    if df is not None:
        engine = FactorEngine()
        factors = engine.calculate(df)

        print("=" * 50)
        print("因子计算结果")
        print("=" * 50)

        for name, data in factors.items():
            if name == "summary":
                print(f"\n【综合评分】")
                print(f"  整体评分: {data['overall_score']}")
                print(f"  看多信号: {data['bullish_signals']}")
                print(f"  看空信号: {data['bearish_signals']}")
            else:
                print(f"\n【{name.upper()}因子】")
                for key, value in list(data.items())[:5]:
                    print(f"  {key}: {value}")
