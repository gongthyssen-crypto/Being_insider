from __future__ import annotations

import argparse
import sys

from app.knowledge_base import (
    SCENARIO_KNOWLEDGE_DIRS,
    build_all_embedding_indexes,
    build_scenario_embedding_index,
    current_knowledge_retrieval_mode,
    is_embedding_configured,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build persistent embedding indexes for scenario knowledge bases."
    )
    parser.add_argument(
        "--scenario",
        choices=sorted(SCENARIO_KNOWLEDGE_DIRS.keys()),
        help="Build only one scenario index.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Build indexes for all scenarios.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild indexes even if the source files have not changed.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not is_embedding_configured():
        print("Embedding service is not configured.")
        print("Set EMBEDDING_BASE_URL and EMBEDDING_MODEL first.")
        return 1

    target_all = args.all or not args.scenario
    try:
        if target_all:
            paths = build_all_embedding_indexes(force=args.force)
        else:
            paths = [build_scenario_embedding_index(args.scenario, force=args.force)]
    except Exception as exc:
        print(f"Index build failed: {exc}")
        return 1

    print(f"Knowledge retrieval mode: {current_knowledge_retrieval_mode()}")
    for path in paths:
        print(f"Built index: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
