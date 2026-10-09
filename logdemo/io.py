"""Read and validate JSON Lines log events."""

import json

LEVELS = ("INFO", "WARN", "ERROR")


class InputError(Exception):
    """Raised when a log file cannot be read or contains an invalid event."""


def read_events(path: str) -> list[dict[str, str]]:
    """Return validated events from a JSON Lines file, ignoring blank lines."""
    try:
        with open(path, encoding="utf-8") as handle:
            lines = handle.readlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise InputError(f"{path}: cannot read file: {exc.__class__.__name__}") from exc

    events = []
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except (json.JSONDecodeError, RecursionError) as exc:
            raise InputError(f"{path}:{number}: invalid JSON") from exc
        events.append(_validate(record, f"{path}:{number}"))
    return events


def _validate(record: object, where: str) -> dict[str, str]:
    if not isinstance(record, dict):
        raise InputError(f"{where}: event must be a JSON object")
    service = record.get("service")
    if not isinstance(service, str) or not service:
        raise InputError(f"{where}: 'service' must be a nonempty string")
    level = record.get("level")
    if level not in LEVELS:
        raise InputError(f"{where}: 'level' must be one of INFO, WARN, ERROR")
    message = record.get("message")
    if not isinstance(message, str):
        raise InputError(f"{where}: 'message' must be a string")
    return {"service": service, "level": level, "message": message}
