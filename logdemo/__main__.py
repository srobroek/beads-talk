"""Command-line entry point: python3 -m logdemo."""

import argparse
import json
import sys

from logdemo.io import InputError, read_events


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="logdemo", description="Analyse JSON Lines logs.")
    commands = parser.add_subparsers(dest="command", required=True)
    dump = commands.add_parser("dump", help="print validated events as a JSON array")
    dump.add_argument("file")
    args = parser.parse_args(argv)

    try:
        events = read_events(args.file)
    except InputError as exc:
        print(f"logdemo: error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(events, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
