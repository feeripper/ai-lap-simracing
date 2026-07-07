"""Script to add a reference lap to the database."""

from __future__ import annotations

import sys
from pathlib import Path

import argparse
from sqlalchemy.orm import Session

from src.db import SessionLocal, init_db
from src.db.models import ReferenceLap
from src.db.repository import (
    create_reference_lap,
    get_car_by_name,
    get_simulator_by_name,
    get_track_by_name,
)


class CSVFileNotFoundError(Exception):
    """Raised when the CSV file does not exist."""


class SeedNotRunError(Exception):
    """Raised when the database has not been seeded."""


def add_reference_lap_to_db(
    db: Session, csv_path: str, driver_name: str, lap_time_seconds: float
) -> ReferenceLap:
    """Add a reference lap to the database for iRacing + Toyota GR86 + Spa.

    Args:
        db: SQLAlchemy session
        csv_path: Path to the CSV file
        driver_name: Name of the reference driver
        lap_time_seconds: Lap time in seconds

    Returns:
        The created ReferenceLap object

    Raises:
        CSVFileNotFoundError: If the CSV file does not exist
        SeedNotRunError: If iRacing, Toyota GR86, or Spa are not found in database
    """
    # Validate CSV file exists
    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise CSVFileNotFoundError(f"CSV file not found: {csv_path}")

    # Get simulator, car, and track (fixed for MVP)
    simulator = get_simulator_by_name(db, "iRacing")
    if not simulator:
        raise SeedNotRunError("Simulator 'iRacing' not found in database. Please run: python scripts/seed_db.py")

    car = get_car_by_name(db, "Toyota GR86")
    if not car:
        raise SeedNotRunError("Car 'Toyota GR86' not found in database. Please run: python scripts/seed_db.py")

    track = get_track_by_name(db, "Spa")
    if not track:
        raise SeedNotRunError("Track 'Spa' not found in database. Please run: python scripts/seed_db.py")

    # Create reference lap (this will deactivate any existing active lap)
    reference_lap = create_reference_lap(
        db,
        simulator_id=simulator.id,
        car_id=car.id,
        track_id=track.id,
        driver_name=driver_name,
        lap_time_seconds=lap_time_seconds,
        csv_path=str(csv_file.absolute()),
        is_active=True,
    )

    return reference_lap


def add_reference_lap(csv_path: str, driver_name: str, lap_time_seconds: float) -> None:
    """CLI wrapper to add a reference lap to the database."""
    db = SessionLocal()

    try:
        # Get or ensure database is initialized
        init_db()

        reference_lap = add_reference_lap_to_db(db, csv_path, driver_name, lap_time_seconds)

        print("Reference lap added successfully!")
        print(f"  Driver: {reference_lap.driver_name}")
        print(f"  Lap time: {reference_lap.lap_time_seconds}s")
        print(f"  CSV: {reference_lap.csv_path}")

    except CSVFileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except SeedNotRunError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


def main() -> None:
    """Parse command line arguments and add reference lap."""
    parser = argparse.ArgumentParser(
        description="Add a reference lap to the database for iRacing + Toyota GR86 + Spa"
    )
    parser.add_argument("csv_path", help="Path to the Garage61 CSV file")
    parser.add_argument("driver_name", help="Name of the reference driver")
    parser.add_argument(
        "lap_time_seconds",
        type=float,
        help="Lap time in seconds (e.g., 145.234)",
    )

    args = parser.parse_args()

    add_reference_lap(args.csv_path, args.driver_name, args.lap_time_seconds)


if __name__ == "__main__":
    main()
