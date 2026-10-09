"""Count log events per severity level."""

from logdemo.io import LEVELS


def summarize(events: list[dict[str, str]]) -> dict[str, int]:
    """Return INFO, WARN and ERROR counts in that order, including zeros."""
    counts = dict.fromkeys(LEVELS, 0)
    for event in events:
        if "ERROR" in event["message"]:
            counts["ERROR"] += 1
        else:
            counts[event["level"]] += 1
    return counts
