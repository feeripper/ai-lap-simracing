"""CLI script to analyze a user lap against a reference lap."""

from __future__ import annotations

import argparse
import json
import sys

from src.analysis.pipeline import analyze_lap_files


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the analyze_lap script."""
    parser = argparse.ArgumentParser(
        description="Analyze a user lap against a reference lap from CSV files."
    )
    parser.add_argument(
        "user_csv_path",
        help="Path to the user's lap CSV file"
    )
    parser.add_argument(
        "reference_csv_path",
        help="Path to the reference lap CSV file"
    )
    parser.add_argument(
        "--distance-column",
        default="lap_dist_pct",
        help="Name of the column containing lap distance percentage (default: lap_dist_pct)"
    )
    parser.add_argument(
        "--num-points",
        type=int,
        default=101,
        help="Number of points to normalize to (default: 101)"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the analyze_lap script.

    Args:
        argv: Command line arguments. If None, uses sys.argv[1:].

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = analyze_lap_files(
            user_csv_path=args.user_csv_path,
            reference_csv_path=args.reference_csv_path,
            distance_column=args.distance_column,
            num_points=args.num_points,
        )

        # Print result as formatted JSON
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    except Exception as e:
        # Print error to stderr
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
