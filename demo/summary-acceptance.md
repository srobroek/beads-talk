# Summary acceptance

Contract for `python3 -m logdemo summary FILE`. The CLI JSON values and key order
below are the contract; `checks/acceptance.py summary` exercises it through a
real subprocess. JSON whitespace is not part of the contract.

Each event is counted by its `level` field only. Output always contains the keys
`INFO`, `WARN`, `ERROR`, in that order, zeros included. Exit status 0.

| Input | INFO | WARN | ERROR | Case |
|---|---|---|---|---|
| `fixtures/ordinary.jsonl` | 1 | 1 | 1 | ordinary |
| `fixtures/demo.jsonl` | 2 | 1 | 1 | full |
| `fixtures/message-error.jsonl` | 1 | 0 | 0 | message boundary |

Message boundary: an `INFO` event whose `message` contains `ERROR` counts as
`INFO`. The message text never changes the count.

Invalid input (bad JSON, missing or wrong-typed field, unknown level, unreadable
file) prints a concise error to stderr and exits 2 without a traceback.

Command:

```sh
python3 checks/acceptance.py summary
```
