from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
from .backtester import Backtester
from .signal_validator import SignalValidator
from .factor_analyzer import FactorAnalyzer
from .simulator import Simulator


class ValidationEngine:
    def __init__(self):
        self.backtester = Backtester()
        self.signal_validator = SignalValidator()
        self.factor_analyzer = FactorAnalyzer()
        self.simulator = Simulator()

    def validate_single_stock(
        self,
        df: pd.DataFrame,
        factors: Dict[str, Any] = None,
        signals: Dict[str, Any] = None,
        leader_result: Dict[str, Any] = None,
        code: str = "TEST"
    ) -> Dict[str, Any]:
        results = {
            "code": code,
            "date_range": {
                "start": str(df["date"].min()),
                "end": str(df["date"].max()),
                "days": len(df)
            },
            "factor_analysis": None,
            "signal_validation": None,
            "backtest_result": None,
            "leader_analysis": None
        }

        if factors:
            factor_results = self._analyze_factors_for_df(df, factors)
            results["factor_analysis"] = factor_results

        if signals:
            signal_val = self._validate_signals_for_df(df, signals)
            results["signal_validation"] = signal_val

            bt_result = self._run_backtest(df, signals, code)
            results["backtest_result"] = bt_result

        if leader_result:
            leader_analysis = self._analyze_leader(leader_result, df)
            results["leader_analysis"] = leader_analysis

        return results

    def validate_multiple_stocks(
        self,
        stock_data_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        all_results = []
        
        for stock in stock_data_list:
            df = stock.get("df")
            if df is None or len(df) == 0:
                continue

            result = self.validate_single_stock(
                df=df,
                factors=stock.get("factors"),
                signals=stock.get("signals"),
                leader_result=stock.get("leader_result"),
                code=stock.get("code", "unknown")
            )
            result["name"] = stock.get("name", "")
            all_results.append(result)

        summary = self._generate_portfolio_summary(all_results)

        return {
            "total_stocks": len(all_results),
            "detailed_results": all_results,
            "summary": summary
        }

    def _analyze_factors_for_df(self, df: pd.DataFrame, factors: Dict[str, Any]) -> Dict[str, Any]:
        try:
            factor_values = {}
            
            for name, data in factors.items():
                if name == "summary":
                    continue
                if isinstance(data, dict):
                    if "score" in data:
                        factor_values[name] = pd.Series([data["score"]] * len(df))
                    elif "trend_strength" in data:
                        factor_values[name] = pd.Series([data["trend_strength"]] * len(df))
                    elif "combined_strength" in data:
                        factor_values[name] = pd.Series([data["combined_strength"]] * len(df))
                    else:
                        continue
                else:
                    factor_values[name] = pd.Series(data)

            return self.factor_analyzer.analyze_multiple_factors(df, factor_values)
        except Exception as e:
            return {"error": str(e)}

    def _validate_signals_for_df(self, df: pd.DataFrame, signals: Dict[str, Any]) -> Dict[str, Any]:
        try:
            df_with_signals = df.copy()
            df_with_signals["signal"] = ""
            df_with_signals["direction"] = "neutral"

            if "summary" in signals:
                summary = signals["summary"]
                df_with_signals.loc[len(df) - 1, "signal"] = summary.get("overall_direction", "")
                df_with_signals.loc[len(df) - 1, "direction"] = summary.get("overall_direction", "neutral")

            return self.signal_validator.validate_signal(df_with_signals)
        except Exception as e:
            return {"error": str(e)}

    def _run_backtest(self, df: pd.DataFrame, signals: Dict[str, Any], code: str) -> Dict[str, Any]:
        def signal_generator(df: pd.DataFrame, index: int) -> Optional[Dict[str, Any]]:
            if "summary" in signals:
                summary = signals["summary"]
                if summary.get("overall_direction") == "bullish":
                    return {
                        "direction": "bullish",
                        "signal": summary.get("overall_direction", ""),
                        "strength": summary.get("overall_strength", 50)
                    }
            return None

        return self.backtester.run(df, signal_generator, code)

    def _analyze_leader(self, leader_result: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        analysis = {
            "is_leader": leader_result.get("is_leader", False),
            "leader_score": leader_result.get("leader_score", 0),
            "leader_type": leader_result.get("leader_type", "普通"),
            "reasons": leader_result.get("reason", []),
            "metadata": leader_result.get("metadata", {})
        }

        if len(df) >= 5:
            recent_returns = df["close"].pct_change(5).iloc[-1] * 100
            analysis["recent_5d_return"] = recent_returns

        return analysis

    def _generate_portfolio_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not results:
            return {}

        valid_results = [r for r in results if r.get("backtest_result")]
        
        if not valid_results:
            return {
                "total_stocks_analyzed": len(results),
                "total_stocks_with_backtest": 0
            }

        total_returns = [r["backtest_result"]["total_return"] for r in valid_results]
        win_rates = [r["backtest_result"].get("win_rate", 0) for r in valid_results]
        max_drawdowns = [r["backtest_result"].get("max_drawdown", 0) for r in valid_results]
        sharpes = [r["backtest_result"].get("sharpe_ratio", 0) for r in valid_results]

        leader_count = sum(1 for r in results if r.get("leader_analysis", {}).get("is_leader", False))

        return {
            "total_stocks_analyzed": len(results),
            "total_stocks_with_backtest": len(valid_results),
            "avg_total_return": np.mean(total_returns),
            "avg_win_rate": np.mean(win_rates),
            "avg_max_drawdown": np.mean(max_drawdowns),
            "avg_sharpe_ratio": np.mean(sharpes),
            "best_return": max(total_returns),
            "worst_return": min(total_returns),
            "leader_count": leader_count,
            "leader_ratio": leader_count / len(results) * 100
        }

    def generate_report(self, validation_result: Dict[str, Any]) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("系统有效性验证报告")
        lines.append("=" * 60)
        lines.append("")

        summary = validation_result.get("summary", {})
        lines.append(f"分析股票总数: {summary.get('total_stocks_analyzed', 0)}")
        lines.append(f"进行回测股票: {summary.get('total_stocks_with_backtest', 0)}")
        lines.append("")

        lines.append("【回测统计】")
        lines.append(f"平均总收益: {summary.get('avg_total_return', 0):.2f}%")
        lines.append(f"平均胜率: {summary.get('avg_win_rate', 0):.1f}%")
        lines.append(f"平均最大回撤: {summary.get('avg_max_drawdown', 0):.1f}%")
        lines.append(f"平均夏普比率: {summary.get('avg_sharpe_ratio', 0):.2f}")
        lines.append(f"最佳收益: {summary.get('best_return', 0):.2f}%")
        lines.append(f"最差收益: {summary.get('worst_return', 0):.2f}%")
        lines.append("")

        lines.append("【龙头识别统计】")
        lines.append(f"识别为龙头的股票: {summary.get('leader_count', 0)}")
        lines.append(f"龙头占比: {summary.get('leader_ratio', 0):.1f}%")
        lines.append("")

        if validation_result.get("detailed_results"):
            lines.append("【各股票分析】")
            for stock in validation_result["detailed_results"][:5]:
                lines.append(f"- {stock.get('code', '?')}:")
                if stock.get("backtest_result"):
                    bt = stock["backtest_result"]
                    lines.append(f"  收益: {bt.get('total_return', 0):.1f}%  胜率: {bt.get('win_rate', 0):.1f}%")
                if stock.get("leader_analysis"):
                    la = stock["leader_analysis"]
                    lines.append(f"  龙头: {'是' if la.get('is_leader') else '否'}  评分: {la.get('leader_score', 0)}")

        return "\n".join(lines)
