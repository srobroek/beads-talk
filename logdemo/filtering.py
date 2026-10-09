"""Select log events by service."""


def filter_service(events: list[dict[str, str]], service: str) -> list[dict[str, str]]:
    """Return events whose service equals ``service`` exactly, in input order."""
    return [event for event in events if event["service"] == service]
