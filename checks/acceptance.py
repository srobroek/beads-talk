"""Black-box acceptance checks that run the real logdemo CLI.

Usage: python3 checks/acceptance.py baseline|summary|filtered
"""

import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = "fixtures/demo.jsonl"


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "logdemo", *args],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )


def counts(info: int, warn: int, error: int) -> dict[str, int]:
    return {"INFO": info, "WARN": warn, "ERROR": error}


def expect_json(name: str, args: list[str], expected) -> bool:
    result = run(*args)
    observed = None
    if result.returncode == 0:
        try:
            observed = json.loads(result.stdout)
        except json.JSONDecodeError:
            observed = None
    ok = result.returncode == 0 and observed == expected
    # Key order is part of the summary contract.
    if ok and isinstance(expected, dict):
        ok = list(observed) == list(expected)
    report(name, ok, f"expected exit 0 and {json.dumps(expected)}; "
           f"observed exit {result.returncode} stdout={result.stdout.strip()!r} stderr={result.stderr.strip()!r}")
    return ok


def expect_error(name: str, args: list[str]) -> bool:
    result = run(*args)
    ok = result.returncode == 2 and result.stderr.strip() != "" and "Traceback" not in result.stderr
    report(name, ok, f"expected exit 2 with concise stderr; observed exit {result.returncode} stderr={result.stderr.strip()!r}")
    return ok


def report(name: str, ok: bool, detail: str) -> None:
    print(f"{'PASS' if ok else 'FAIL'} {name}" + ("" if ok else f": {detail}"))


def baseline(tmp: str) -> list[bool]:
    demo = [
        {"service": "api", "level": "INFO", "message": "started"},
        {"service": "api", "level": "ERROR", "message": "timeout"},
        {"service": "worker", "level": "WARN", "message": "retrying"},
        {"service": "worker", "level": "INFO", "message": "ERROR budget remains healthy"},
    ]
    malformed = os.path.join(tmp, "malformed.jsonl")
    with open(malformed, "w", encoding="utf-8") as handle:
        handle.write('{"service": "api", "level": "FATAL", "message": "x"}\n')
    return [
        expect_json("dump demo", ["dump", DEMO], demo),
        expect_json("dump empty", ["dump", empty_file(tmp)], []),
        expect_error("dump malformed", ["dump", malformed]),
        expect_error("dump missing file", ["dump", os.path.join(tmp, "missing.jsonl")]),
    ]


def summary(tmp: str) -> list[bool]:
    return [
        expect_json("summary ordinary", ["summary", "fixtures/ordinary.jsonl"], counts(1, 1, 1)),
        expect_json("summary demo", ["summary", DEMO], counts(2, 1, 1)),
        expect_json("summary message boundary", ["summary", "fixtures/message-error.jsonl"], counts(1, 0, 0)),
    ]


def filtered(tmp: str) -> list[bool]:
    return [
        expect_json("filtered api", ["summary", DEMO, "--service", "api"], counts(1, 0, 1)),
        expect_json("filtered worker", ["summary", DEMO, "--service", "worker"], counts(1, 1, 0)),
        expect_json("filtered missing service", ["summary", DEMO, "--service", "billing"], counts(0, 0, 0)),
        expect_json("filtered empty input", ["summary", empty_file(tmp), "--service", "api"], counts(0, 0, 0)),
    ]


def empty_file(tmp: str) -> str:
    path = os.path.join(tmp, "empty.jsonl")
    open(path, "w", encoding="utf-8").close()
    return path


SUITES = {"baseline": baseline, "summary": summary, "filtered": filtered}


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in SUITES:
        print("usage: acceptance.py baseline|summary|filtered", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory() as tmp:
        results = SUITES[argv[0]](tmp)
    print(f"{argv[0]}: {sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
