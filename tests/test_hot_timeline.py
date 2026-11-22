import unittest

from modules.hot_timeline import generate_hot_timeline


class TimelineTests(unittest.TestCase):
    def test_daily_sector_values_must_not_become_intraday_events(self):
        self.assertEqual(generate_hot_timeline([{"name": "算力", "change_pct": 8.8}], {"limit_up_count": 90}), [])
        self.assertEqual(generate_hot_timeline([], None), [])

    def test_missing_source_time_or_attribution_is_rejected(self):
        events = [
            {"time": "10:12", "event": "证券板块异动",
             "source": "https://example.org/report", "source_time": "2026-11-20T10:12:00+08:00"},
            {"time": "09:35", "event": "无来源", "source_time": "2026-11-20T09:35:00+08:00"},
            {"time": "14:00", "event": "无时区", "source": "https://example.org/report",
             "source_time": "2026-11-20T14:00:00"},
        ]
        out = generate_hot_timeline(verified_events=events)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["time"], "10:12")

    def test_stable_sorted_and_limited(self):
        def item(t):
            return {"time": t, "event": "有来源的事件",
                    "source": "https://example.org/evt",
                    "source_time": f"2026-11-20T{t}:00+08:00"}
        out = generate_hot_timeline(verified_events=[item("10:20"), item("09:40")], stock_count=1)
        self.assertEqual([x["time"] for x in out], ["09:40"])


if __name__ == "__main__":
    unittest.main()
