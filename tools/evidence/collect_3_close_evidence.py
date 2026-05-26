from __future__ import annotations

import argparse
from collections.abc import Sequence


FAIL_CLOSED_MESSAGE = (
    "3-close evidence collection is not approved: a future provider implementation "
    "and explicit evidence-collection gate are required before data fetching."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Scaffold for future 3-close evidence collection. This command does not "
            "fetch market data in the current phase."
        )
    )
    parser.add_argument("--symbols", nargs="+", required=True)
    parser.add_argument("--timeframe", required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--max-examples", type=int, default=10)
    parser.add_argument("--output-path", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    parser.error(FAIL_CLOSED_MESSAGE)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
