"""Command-line entry point: python3 -m logdemo."""

import argparse
import json
import sys

from logdemo.filtering import filter_service
from logdemo.io import InputError, read_events
from logdemo.summary import summarize


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="logdemo", description="Analyse JSON Lines logs.")
    commands = parser.add_subparsers(dest="command", required=True)
    dump = commands.add_parser("dump", help="print validated events as a JSON array")
    dump.add_argument("file")
    summary = commands.add_parser("summary", help="count events per severity level")
    summary.add_argument("file")
    summary.add_argument("--service", metavar="NAME", help="summarize only events from this service")
    args = parser.parse_args(argv)

    try:
        events = read_events(args.file)
    except InputError as exc:
        print(f"logdemo: error: {exc}", file=sys.stderr)
        return 2

    if args.command == "summary":
        if args.service is not None:
            events = filter_service(events, args.service)
        print(json.dumps(summarize(events), indent=2))
    else:
        print(json.dumps(events, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
