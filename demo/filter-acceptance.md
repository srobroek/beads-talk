# Filter acceptance

Contract for service filtering. The CLI JSON values and key order below are the
contract; `checks/acceptance.py filtered` exercises it through a real subprocess.
JSON whitespace is not part of the contract.

## Function

`logdemo/filtering.py`:

```python
filter_service(events: list[dict[str, str]], service: str) -> list[dict[str, str]]
```

- Keeps events whose `service` equals `service` exactly (case-sensitive).
- Preserves input order.
- Returns `[]` when nothing matches.

Unit tests live in `tests/test_filtering.py` and cover equality, order and no match.

## CLI

`python3 -m logdemo summary FILE --service NAME` summarizes only matching events.
Keys `INFO`, `WARN`, `ERROR` in that order, zeros included. Exit status 0.

| Input | Service | INFO | WARN | ERROR |
|---|---|---|---|---|
| `fixtures/demo.jsonl` | `api` | 1 | 0 | 1 |
| `fixtures/demo.jsonl` | `worker` | 1 | 1 | 0 |
| `fixtures/demo.jsonl` | `missing` | 0 | 0 | 0 |
| empty file | `api` | 0 | 0 | 0 |

## Ownership

- Filter implementation: `logdemo/filtering.py`, `tests/test_filtering.py`.
- Integration: `logdemo/__main__.py` CLI wiring and `.github/workflows/ci.yml`.
- Out of scope: servers, persistence, pagination, telemetry, unrelated refactors.

Command:

```sh
python3 checks/acceptance.py filtered
```
