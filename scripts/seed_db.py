"""Seed script to populate the database with initial MVP data."""

from __future__ import annotations

import sys

from src.db import SessionLocal, init_db
from src.db.models import Car, Simulator, Track
from src.db.repository import (
    create_car,
    create_reference_lap,
    create_simulator,
    create_track,
    get_car_by_name,
    get_simulator_by_name,
    get_track_by_name,
)


def seed_database() -> None:
    """Seed the database with iRacing, Toyota GR86, and Spa."""
    db = SessionLocal()

    try:
        # Initialize tables
        init_db()
        print("Database tables initialized.")

        # Create or get iRacing simulator
        simulator = get_simulator_by_name(db, "iRacing")
        if not simulator:
            simulator = create_simulator(db, "iRacing")
            print(f"Created simulator: {simulator.name}")
        else:
            print(f"Simulator already exists: {simulator.name}")

        # Create or get Toyota GR86 car
        car = get_car_by_name(db, "Toyota GR86")
        if not car:
            car = create_car(db, "Toyota GR86")
            print(f"Created car: {car.name}")
        else:
            print(f"Car already exists: {car.name}")

        # Create or get Spa track
        track = get_track_by_name(db, "Spa")
        if not track:
            # Note: corners_json will be added later when track data is available
            track = create_track(db, "Spa", layout=None, corners_json=None)
            print(f"Created track: {track.name}")
        else:
            print(f"Track already exists: {track.name}")

        print("\nSeed completed successfully!")
        print(f"Simulator ID: {simulator.id}")
        print(f"Car ID: {car.id}")
        print(f"Track ID: {track.id}")
        print("\nNote: No reference lap was created. Add a reference lap using:")
        print("  scripts/add_reference_lap.py <csv_path> <driver_name> <lap_time_seconds>")

    except Exception as e:
        print(f"Error during seed: {e}", file=sys.stderr)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
