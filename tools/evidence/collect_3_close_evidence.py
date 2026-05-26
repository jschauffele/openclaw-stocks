from __future__ import annotations

import argparse
from collections.abc import Sequence

from tools.evidence.read_only_historical_data_adapter import (
    AlpacaEvidenceClientFactory,
    AlpacaEvidenceStockBarsClientFactory,
    CsvStaticHistoricalCloseProvider,
    EvidenceHistoricalCloseRequest,
    build_alpaca_evidence_provider,
    get_close_bars_for_request,
)
from tools.evidence.three_close_evidence_scanner import (
    scan_three_close_evidence_candidates,
    write_evidence_candidates_json,
)


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
    parser.add_argument("--provider", required=True)
    parser.add_argument("--input-path")
    parser.add_argument("--alpaca-api-key")
    parser.add_argument("--alpaca-secret-key")
    parser.add_argument("--alpaca-data-url")
    parser.add_argument("--enable-alpaca-collection", action="store_true")
    parser.add_argument("--symbols", nargs="+", required=True)
    parser.add_argument("--timeframe", required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--max-examples", type=int, default=10)
    parser.add_argument("--max-bars", type=int)
    parser.add_argument("--output-path", required=True)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    alpaca_client_factory: AlpacaEvidenceClientFactory | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.provider == "alpaca" and not args.enable_alpaca_collection:
        parser.error(FAIL_CLOSED_MESSAGE)
    if args.provider not in {"csv", "alpaca"}:
        parser.error(FAIL_CLOSED_MESSAGE)

    provider = _build_provider(args, parser, alpaca_client_factory)
    source_provider = _source_provider_label(args)
    candidates = []
    for symbol in args.symbols:
        request = EvidenceHistoricalCloseRequest(
            symbol=symbol,
            timeframe=args.timeframe,
            start=args.start_date,
            end=args.end_date,
            max_bars=args.max_bars,
        )
        bars = get_close_bars_for_request(provider, request)
        candidates.extend(
            scan_three_close_evidence_candidates(
                symbol=request.symbol,
                timeframe=request.timeframe,
                bars=bars,
                source_provider=source_provider,
                evidence_type="historical",
                max_examples=args.max_examples,
            )
        )

    write_evidence_candidates_json(candidates[: args.max_examples], args.output_path)
    return 0


def _build_provider(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    alpaca_client_factory: AlpacaEvidenceClientFactory | None,
):
    if args.provider == "csv":
        if not args.input_path or not args.input_path.strip():
            parser.error("--input-path is required for --provider csv")
        return CsvStaticHistoricalCloseProvider(args.input_path)

    if not args.alpaca_api_key or not args.alpaca_secret_key:
        parser.error("--alpaca-api-key and --alpaca-secret-key are required")
    return build_alpaca_evidence_provider(
        api_key=args.alpaca_api_key,
        secret_key=args.alpaca_secret_key,
        data_url=args.alpaca_data_url,
        client_factory=alpaca_client_factory or AlpacaEvidenceStockBarsClientFactory(),
    )


def _source_provider_label(args: argparse.Namespace) -> str:
    if args.provider == "csv":
        return f"csv:{args.input_path}"
    if args.provider == "alpaca":
        return "alpaca:iex"
    raise ValueError(f"unsupported provider: {args.provider}")


if __name__ == "__main__":
    raise SystemExit(main())
