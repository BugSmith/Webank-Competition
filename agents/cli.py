"""Command line helpers for running the Webank agent pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from agents.pipeline import WebankAgentPipeline, build_default_pipeline
from agents.conversation import ConversationService


def _load_payload(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Input payload not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_output(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_pipeline(args: argparse.Namespace) -> None:
    payload = _load_payload(Path(args.input))
    pipeline = build_default_pipeline(model_id=args.model)
    result = pipeline.run(payload)

    if args.output:
        _write_output(Path(args.output), result)

    if args.user_id:
        service = ConversationService()
        service.persist_pipeline_output(args.user_id, result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Utilities for Webank multi-agent pipeline and persistence.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "refresh-insights",
        help="Run the agent pipeline for a JSON payload and optionally persist the result.",
    )
    run_parser.add_argument(
        "--input",
        required=True,
        help="Path to the pipeline input JSON.",
    )
    run_parser.add_argument(
        "--output",
        help="Optional path to dump the pipeline output JSON.",
    )
    run_parser.add_argument(
        "--user-id",
        help="Persist the pipeline result for the specified user (writes to MySQL).",
    )
    run_parser.add_argument(
        "--model",
        help="Override the default model identifier configured via env vars.",
    )
    run_parser.set_defaults(func=run_pipeline)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
