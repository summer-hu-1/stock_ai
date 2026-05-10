from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class FactorAnalyzer:
    def __init__(self):
        pass

    def _pearson_correlation(self, x: pd.Series, y: pd.Series) -> float:
        x_mean = x.mean()
        y_mean = y.mean()
        
        numerator = ((x - x_mean) * (y - y_mean)).sum()
        denominator = np.sqrt(((x - x_mean) ** 2).sum() * ((y - y_mean) ** 2).sum())
        
        if denominator == 0:
            return 0.0
        return numerator / denominator

    def _spearman_correlation(self, x: pd.Series, y: pd.Series) -> float:
        x_rank = x.rank()
        y_rank = y.rank()
        
        return self._pearson_correlation(x_rank, y_rank)

    def analyze_factor(
        self,
        df: pd.DataFrame,
        factor_values: pd.Series,
        lookahead_returns: int = 5,
        quantiles: int = 5
    ) -> Dict[str, Any]:
        df = df.copy()
        df["factor"] = factor_values.values

        df["lookahead_return"] = df["close"].pct_change(lookahead_returns).shift(-lookahead_returns)

        valid_df = df.dropna(subset=["factor", "lookahead_return"])

        if len(valid_df) < 10:
            return {"error": "Insufficient data"}

        valid_df["quantile"] = pd.qcut(valid_df["factor"], quantiles, labels=False)

        quantile_results = []
        for q in range(quantiles):
            q_df = valid_df[valid_df["quantile"] == q]
            if len(q_df) > 0:
                quantile_results.append({
                    "quantile": q + 1,
                    "count": len(q_df),
                    "avg_return": q_df["lookahead_return"].mean() * 100,
                    "std_return": q_df["lookahead_return"].std() * 100,
                    "win_rate": (q_df["lookahead_return"] > 0).mean() * 100,
                    "factor_mean": q_df["factor"].mean()
                })

        high_q = valid_df[valid_df["quantile"] == quantiles - 1]
        low_q = valid_df[valid_df["quantile"] == 0]

        ic_pearson = self._pearson_correlation(valid_df["factor"], valid_df["lookahead_return"])
        ic_spearman = self._spearman_correlation(valid_df["factor"], valid_df["lookahead_return"])

        return {
            "factor_name": "custom",
            "total_samples": len(valid_df),
            "ic_pearson": ic_pearson,
            "ic_spearman": ic_spearman,
            "quantile_spread": (high_q["lookahead_return"].mean() - low_q["lookahead_return"].mean()) * 100,
            "top_quantile_return": high_q["lookahead_return"].mean() * 100,
            "bottom_quantile_return": low_q["lookahead_return"].mean() * 100,
            "quantile_analysis": quantile_results,
            "correlation_matrix": self._calc_correlation(valid_df[["factor", "lookahead_return"]])
        }

    def analyze_multiple_factors(
        self,
        df: pd.DataFrame,
        factors: Dict[str, pd.Series]
    ) -> Dict[str, Any]:
        results = {}
        
        for factor_name, factor_values in factors.items():
            if isinstance(factor_values, dict):
                if "score" in factor_values:
                    factor_series = pd.Series([factor_values["score"]] * len(df))
                elif "trend_strength" in factor_values:
                    factor_series = pd.Series([factor_values["trend_strength"]] * len(df))
                else:
                    continue
            else:
                factor_series = factor_values

            if len(factor_series) == len(df):
                result = self.analyze_factor(df, factor_series)
                result["factor_name"] = factor_name
                results[factor_name] = result

        factor_df = pd.DataFrame({
            name: self._extract_factor_score(factors[name])
            for name in results.keys()
        })

        correlation_matrix = factor_df.corr()

        return {
            "factor_analysis": results,
            "correlation_matrix": correlation_matrix.to_dict(),
            "summary": self._generate_summary(results)
        }

    def _extract_factor_score(self, factor_data) -> pd.Series:
        if isinstance(factor_data, dict):
            if "score" in factor_data:
                return pd.Series(factor_data["score"])
            elif "trend_strength" in factor_data:
                return pd.Series(factor_data["trend_strength"])
            elif isinstance(factor_data.get("values"), list):
                return pd.Series(factor_data["values"])
        return pd.Series(dtype=float)

    def _calc_correlation(self, df: pd.DataFrame) -> Dict[str, Any]:
        corr = df.corr().to_dict()
        return corr

    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        if not results:
            return {}

        ics_pearson = [r["ic_pearson"] for r in results.values() if "ic_pearson" in r]
        ics_spearman = [r["ic_spearman"] for r in results.values() if "ic_spearman" in r]
        spreads = [r["quantile_spread"] for r in results.values() if "quantile_spread" in r]

        best_factor = max(results.items(), key=lambda x: abs(x[1].get("ic_pearson", 0)))
        worst_factor = min(results.items(), key=lambda x: abs(x[1].get("ic_pearson", 0)))

        return {
            "num_factors": len(results),
            "avg_ic_pearson": np.mean(ics_pearson),
            "avg_ic_spearman": np.mean(ics_spearman),
            "avg_quantile_spread": np.mean(spreads),
            "best_factor": {"name": best_factor[0], "ic": best_factor[1].get("ic_pearson", 0)},
            "worst_factor": {"name": worst_factor[0], "ic": worst_factor[1].get("ic_pearson", 0)}
        }

    def calculate_ic(
        self,
        df: pd.DataFrame,
        factor_values: pd.Series,
        lookahead_days: int = 5
    ) -> float:
        df = df.copy()
        df["factor"] = factor_values.values
        df["lookahead_return"] = df["close"].pct_change(lookahead_days).shift(-lookahead_days)
        
        valid_df = df.dropna(subset=["factor", "lookahead_return"])
        if len(valid_df) < 2:
            return 0.0
        
        return self._spearman_correlation(valid_df["factor"], valid_df["lookahead_return"])
