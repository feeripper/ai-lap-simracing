"""CLI to sync reference laps from Garage61 into the local database.

Usage:
    python -m scripts.sync_reference_laps --simulator "iRacing" --car "Toyota GR86" \
        --track "Spa" --limit 5

By default this does NOT activate any collected reference lap. Pass --activate-best to
activate the fastest validated collected lap for the combination.

This script never performs HTML scraping or browser automation. It relies on an optional
Garage61 client dependency and the GARAGE61_ACCESS_TOKEN environment variable.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from sqlalchemy.orm import Session

from src.db import SessionLocal, init_db
from src.db.models import ReferenceLap
from src.reference_collectors.exceptions import (
    Garage61CandidateNotFoundError,
    Garage61CsvDownloadError,
    Garage61CsvValidationError,
    Garage61DependencyMissingError,
    Garage61TokenMissingError,
    ReferenceCollectorError,
)
from src.reference_collectors.garage61_collector import Garage61ReferenceCollector


def run_sync(
    db: Session,
    simulator: str,
    car: str,
    track: str,
    limit: int = 5,
    activate_best: bool = False,
    collector: Optional[Garage61ReferenceCollector] = None,
) -> list[ReferenceLap]:
    """Run the Garage61 reference lap collection and return the collected laps.

    A collector may be injected for testing; otherwise a default
    ``Garage61ReferenceCollector`` (token from env) is used.
    """
    collector = collector or Garage61ReferenceCollector()
    return collector.collect_reference_laps(
        db,
        simulator=simulator,
        car=car,
        track=track,
        limit=limit,
        activate_best=activate_best,
    )


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync reference laps from Garage61 into the local database."
    )
    parser.add_argument("--simulator", required=True, help="Simulator name, e.g. 'iRacing'")
    parser.add_argument("--car", required=True, help="Car name, e.g. 'Toyota GR86'")
    parser.add_argument("--track", required=True, help="Track name, e.g. 'Spa'")
    parser.add_argument(
        "--limit", type=int, default=5, help="Maximum number of candidates to collect"
    )
    parser.add_argument(
        "--activate-best",
        action="store_true",
        help="Activate the fastest validated collected reference lap (off by default).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> None:
    """Parse CLI arguments and run the reference lap sync with clear error messages."""
    args = _parse_args(argv)

    db = SessionLocal()
    try:
        init_db()
        collected = run_sync(
            db,
            simulator=args.simulator,
            car=args.car,
            track=args.track,
            limit=args.limit,
            activate_best=args.activate_best,
        )
    except Garage61TokenMissingError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        print(
            "Hint: set the GARAGE61_ACCESS_TOKEN environment variable (see .env.example).",
            file=sys.stderr,
        )
        db.rollback()
        sys.exit(1)
    except Garage61DependencyMissingError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        db.rollback()
        sys.exit(1)
    except Garage61CandidateNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        db.rollback()
        sys.exit(1)
    except (Garage61CsvDownloadError, Garage61CsvValidationError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        db.rollback()
        sys.exit(1)
    except ReferenceCollectorError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        db.rollback()
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001 - top-level CLI safety net
        print(f"Unexpected error: {exc}", file=sys.stderr)
        db.rollback()
        sys.exit(1)
    else:
        print(f"Collected {len(collected)} reference lap(s) from Garage61:")
        for lap in collected:
            active_flag = " [ACTIVE]" if lap.is_active else ""
            print(
                f"  - id={lap.id} driver='{lap.driver_name}' "
                f"time={lap.lap_time_seconds}s status={lap.validation_status}"
                f" source_lap_id={lap.source_lap_id}{active_flag}"
            )
        if not args.activate_best:
            print("\nNo reference lap was activated (use --activate-best to activate).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
