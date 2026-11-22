"""Display only timestamped and sourced market events, never invented intraday action.

Earlier implementation mapped daily sector percentages to fixed times and randomly
selected leader stocks. Neither is evidence of an event at that time.
"""
from datetime import datetime
from typing import Dict, List, Optional


def generate_hot_timeline(
    hot_sectors: Optional[List[Dict]] = None,
    sentiment: Optional[Dict] = None,
    stock_count: int = 5,
    verified_events: Optional[List[Dict]] = None,
) -> List[Dict]:
    """Return normalized sourced events; sector/sentiment data alone is insufficient.

    Each event requires time (HH:MM), event text, source URL and source_time
    with explicit UTC offset. This is an attribution completeness check, not
    third-party fact checking. No evidence => no claimed intraday event.
    """
    if not isinstance(stock_count, int) or stock_count < 1:
        raise ValueError("stock_count must be a positive integer")
    result = []
    for raw in (verified_events or []):
        if not isinstance(raw, dict):
            continue
        time_text = raw.get("time")
        event = raw.get("event")
        source = raw.get("source")
        source_time = raw.get("source_time")
        if not all(isinstance(v, str) and v.strip() for v in (time_text, event, source, source_time)):
            continue
        if not source.startswith(("https://", "http://")):
            continue
        try:
            parsed_time = datetime.strptime(time_text, "%H:%M").time()
            parsed_source = datetime.fromisoformat(source_time.replace("Z", "+00:00"))
            if parsed_source.tzinfo is None or not ("09:30" <= time_text <= "15:00"):
                continue
        except ValueError:
            continue
        result.append({
            "time": parsed_time.strftime("%H:%M"),
            "event": event.strip(),
            "source": source,
            "source_time": source_time,
            "importance": raw.get("importance", "medium"),
        })
    return sorted(result, key=lambda item: item["time"])[:stock_count]
