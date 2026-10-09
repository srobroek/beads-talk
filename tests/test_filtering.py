import unittest

from logdemo.filtering import filter_service


def event(service: str, level: str = "INFO", message: str = "") -> dict[str, str]:
    return {"service": service, "level": level, "message": message}


class FilterServiceTest(unittest.TestCase):
    def test_keeps_only_exact_matches(self):
        events = [event("api"), event("worker"), event("api-gateway"), event("ap")]
        self.assertEqual(filter_service(events, "api"), [event("api")])

    def test_is_case_sensitive(self):
        events = [event("API"), event("Api"), event("api")]
        self.assertEqual(filter_service(events, "api"), [event("api")])
        self.assertEqual(filter_service(events, "API"), [event("API")])

    def test_preserves_input_order(self):
        events = [
            event("api", "ERROR", "first"),
            event("worker", "WARN", "skip"),
            event("api", "INFO", "second"),
            event("api", "WARN", "third"),
        ]
        self.assertEqual(
            [e["message"] for e in filter_service(events, "api")],
            ["first", "second", "third"],
        )

    def test_returns_empty_list_without_matches(self):
        self.assertEqual(filter_service([event("api"), event("worker")], "missing"), [])
        self.assertEqual(filter_service([], "api"), [])


if __name__ == "__main__":
    unittest.main()
