import unittest

import pandas as pd

from quant_research.engine import Costs, backtest_ma, validate_bars


def rising(n=35):
    close = [float(10 + i) for i in range(n)]
    return pd.DataFrame({
        "date": pd.date_range("2025-01-01", periods=n, freq="B"),
        "open": close,
        "high": [v+1 for v in close],
        "low": [v-1 for v in close],
        "close": close,
        "volume": [1000]*n,
    })


class ResearchTests(unittest.TestCase):
    def test_ascending_dates_and_validation(self):
        x = validate_bars(rising().iloc[::-1])
        self.assertTrue(x.date.is_monotonic_increasing)
        with self.assertRaises(ValueError):
            validate_bars(rising().assign(open=0))
        with self.assertRaises(ValueError):
            validate_bars(pd.concat([rising(), rising().tail(1)]))

    def test_reject_bad_params(self):
        with self.assertRaises(ValueError):
            backtest_ma(rising(), 20, 5)
        with self.assertRaises(ValueError):
            backtest_ma(rising(10), 5, 20)
        with self.assertRaises(ValueError):
            Costs(commission_bps=-2)

    def test_lagged_signal_and_next_open(self):
        x = rising()
        curve, stats = backtest_ma(x, fast=2, slow=4, costs=Costs(0, 0, 0))
        self.assertEqual(curve.signal_date.iloc[0], x.date.iloc[3])
        self.assertEqual(curve.date.iloc[0], x.date.iloc[4])
        self.assertAlmostEqual(curve.entry_open.iloc[0], 14.0)
        self.assertAlmostEqual(curve.next_open.iloc[0], 15.0)
        self.assertEqual(curve.position.iloc[0], 1)
        self.assertEqual(stats["entries"], 1)
        self.assertEqual(stats["exits_including_liquidation"], 1)

    def test_change_current_close_cannot_change_current_signal(self):
        x = rising()
        original, _ = backtest_ma(x, fast=2, slow=4)
        # Manipulate a close at date t, keep it within valid high-low bounds.
        x.loc[9, "close"] = x.loc[9, "open"] - 0.5
        changed, _ = backtest_ma(x, fast=2, slow=4)
        self.assertEqual(int(original.position.iloc[9-4]), int(changed.position.iloc[9-4]))

    def test_costs_reduce_profit(self):
        x = rising()
        free, _ = backtest_ma(x, 2, 4, Costs(0, 0, 0))
        taxed, _ = backtest_ma(x, 2, 4, Costs(3, 5, 5))
        self.assertLess(taxed.equity.iloc[-1], free.equity.iloc[-1])
        self.assertGreater(taxed.cost_return.sum(), 0)

    def test_no_signal_returns_flat(self):
        x = rising()
        x["close"] = x["close"].iloc[::-1].to_numpy()
        x["open"] = x["close"]
        x["high"] = x["open"] + 1
        x["low"] = x["open"] - 1
        curve, summary = backtest_ma(x, 2, 4)
        self.assertEqual(summary["entries"], 0)
        self.assertAlmostEqual(summary["total_return"], 0.0)


if __name__ == "__main__":
    unittest.main()
