"""CLI script to analyze a user lap against the active reference lap from database."""

from __future__ import annotations

import argparse
import json
import sys

from src.analysis.pipeline import analyze_lap_files
from src.db import SessionLocal
from src.db.repository import (
    get_active_reference_lap,
    get_car_by_name,
    get_simulator_by_name,
    get_track_by_name,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the analyze_lap_with_reference script."""
    parser = argparse.ArgumentParser(
        description="Analyze a user lap against the active reference lap from database."
    )
    parser.add_argument(
        "user_csv_path",
        help="Path to the user's lap CSV file"
    )
    parser.add_argument(
        "--simulator",
        required=True,
        help="Simulator name (e.g., iRacing)"
    )
    parser.add_argument(
        "--car",
        required=True,
        help="Car name (e.g., Toyota GR86)"
    )
    parser.add_argument(
        "--track",
        required=True,
        help="Track name (e.g., Spa)"
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
    """Main entry point for the analyze_lap_with_reference script.

    Args:
        argv: Command line arguments. If None, uses sys.argv[1:].

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        # Open database session
        with SessionLocal() as session:
            # Get simulator
            simulator = get_simulator_by_name(session, args.simulator)
            if not simulator:
                print(f"Error: simulator not found: {args.simulator}", file=sys.stderr)
                return 1

            # Get car
            car = get_car_by_name(session, args.car)
            if not car:
                print(f"Error: car not found: {args.car}", file=sys.stderr)
                return 1

            # Get track
            track = get_track_by_name(session, args.track)
            if not track:
                print(f"Error: track not found: {args.track}", file=sys.stderr)
                return 1

            # Get active reference lap
            reference_lap = get_active_reference_lap(
                session,
                simulator_id=simulator.id,
                car_id=car.id,
                track_id=track.id,
            )
            if not reference_lap:
                print(
                    f"Error: active reference lap not found for simulator '{args.simulator}', car '{args.car}', track '{args.track}'",
                    file=sys.stderr,
                )
                return 1

            # Analyze laps
            result = analyze_lap_files(
                user_csv_path=args.user_csv_path,
                reference_csv_path=reference_lap.csv_path,
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
