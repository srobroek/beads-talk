import os
import tempfile
import unittest

from logdemo.io import InputError, read_events

FIXTURES = os.path.join(os.path.dirname(__file__), os.pardir, "fixtures")


def write_temp(text: str) -> str:
    handle = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
    with handle:
        handle.write(text)
    return handle.name


class ReadEventsTest(unittest.TestCase):
    def read_text(self, text: str) -> list[dict[str, str]]:
        path = write_temp(text)
        self.addCleanup(os.remove, path)
        return read_events(path)

    def test_reads_demo_fixture_in_order(self):
        events = read_events(os.path.join(FIXTURES, "demo.jsonl"))
        self.assertEqual(
            [(e["service"], e["level"]) for e in events],
            [("api", "INFO"), ("api", "ERROR"), ("worker", "WARN"), ("worker", "INFO")],
        )

    def test_ignores_blank_lines_and_accepts_empty_input(self):
        self.assertEqual(self.read_text(""), [])
        self.assertEqual(
            self.read_text('\n{"service": "a", "level": "WARN", "message": ""}\n  \n'),
            [{"service": "a", "level": "WARN", "message": ""}],
        )

    def test_rejects_invalid_records(self):
        cases = {
            "invalid JSON": "{not json\n",
            "JSON object": "[]\n",
            "service": '{"service": "", "level": "INFO", "message": "x"}\n',
            "level": '{"service": "a", "level": "DEBUG", "message": "x"}\n',
            "message": '{"service": "a", "level": "INFO", "message": 3}\n',
        }
        for expected, text in cases.items():
            with self.subTest(expected):
                with self.assertRaisesRegex(InputError, expected):
                    self.read_text(text)

    def test_rejects_unreadable_file(self):
        with self.assertRaisesRegex(InputError, "cannot read file"):
            read_events(os.path.join(FIXTURES, "missing.jsonl"))


if __name__ == "__main__":
    unittest.main()
