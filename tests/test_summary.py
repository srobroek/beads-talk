import os
import unittest

from logdemo.io import read_events
from logdemo.summary import summarize

FIXTURES = os.path.join(os.path.dirname(__file__), os.pardir, "fixtures")


def event(level: str, message: str = "ok") -> dict[str, str]:
    return {"service": "api", "level": level, "message": message}


class SummarizeTest(unittest.TestCase):
    def test_counts_ordinary_fixture(self):
        events = read_events(os.path.join(FIXTURES, "ordinary.jsonl"))
        self.assertEqual(summarize(events), {"INFO": 1, "WARN": 1, "ERROR": 1})

    def test_reports_all_levels_in_order_including_zeros(self):
        result = summarize([event("WARN"), event("WARN")])
        self.assertEqual(list(result.items()), [("INFO", 0), ("WARN", 2), ("ERROR", 0)])

    def test_empty_input_counts_zero(self):
        self.assertEqual(summarize([]), {"INFO": 0, "WARN": 0, "ERROR": 0})


if __name__ == "__main__":
    unittest.main()
