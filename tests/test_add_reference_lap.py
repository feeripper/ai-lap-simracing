"""Unit tests for add_reference_lap script."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scripts.add_reference_lap import CSVFileNotFoundError, SeedNotRunError, add_reference_lap_to_db
from src.db.models import Base
from src.db.repository import (
    create_car,
    create_reference_lap,
    create_simulator,
    create_track,
    get_active_reference_lap,
    get_car_by_name,
    get_simulator_by_name,
    get_track_by_name,
)


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def seeded_db(in_memory_db):
    """Seed the database with iRacing, Toyota GR86, and Spa."""
    create_simulator(in_memory_db, "iRacing")
    create_car(in_memory_db, "Toyota GR86")
    create_track(in_memory_db, "Spa")
    return in_memory_db


def test_add_reference_lap_with_valid_csv(seeded_db, tmp_path):
    """Test adding a reference lap with a valid CSV file."""
    # Create a temporary CSV file
    csv_file = tmp_path / "test_lap.csv"
    csv_file.write_text("Speed,LapDistPct,Brake,Throttle\n100,0.5,0,1")

    # Add reference lap using the testable function
    reference_lap = add_reference_lap_to_db(seeded_db, str(csv_file), "TestDriver", 145.5)

    # Verify the reference lap was created
    assert reference_lap.driver_name == "TestDriver"
    assert reference_lap.lap_time_seconds == 145.5
    assert reference_lap.is_active is True

    # Verify it's the active lap in the database
    simulator = get_simulator_by_name(seeded_db, "iRacing")
    car = get_car_by_name(seeded_db, "Toyota GR86")
    track = get_track_by_name(seeded_db, "Spa")

    active_lap = get_active_reference_lap(seeded_db, simulator.id, car.id, track.id)
    assert active_lap is not None
    assert active_lap.id == reference_lap.id


def test_add_reference_lap_with_nonexistent_csv(seeded_db, tmp_path):
    """Test adding a reference lap with a non-existent CSV file."""
    # Try to add reference lap with non-existent file
    with pytest.raises(CSVFileNotFoundError) as exc_info:
        add_reference_lap_to_db(seeded_db, str(tmp_path / "nonexistent.csv"), "TestDriver", 145.5)

    assert "CSV file not found" in str(exc_info.value)


def test_add_reference_lap_without_seed(in_memory_db, tmp_path):
    """Test adding a reference lap when database is not seeded."""
    csv_file = tmp_path / "test_lap.csv"
    csv_file.write_text("Speed,LapDistPct,Brake,Throttle\n100,0.5,0,1")

    # Try to add reference lap without seed
    with pytest.raises(SeedNotRunError) as exc_info:
        add_reference_lap_to_db(in_memory_db, str(csv_file), "TestDriver", 145.5)

    assert "not found in database" in str(exc_info.value)


def test_add_reference_lap_deactivates_previous(seeded_db, tmp_path):
    """Test that adding a new active reference lap deactivates the previous one."""
    # Create first CSV and reference lap
    csv_file1 = tmp_path / "lap1.csv"
    csv_file1.write_text("Speed,LapDistPct,Brake,Throttle\n100,0.5,0,1")

    first_lap = add_reference_lap_to_db(seeded_db, str(csv_file1), "Driver1", 145.0)

    # Create second CSV and reference lap
    csv_file2 = tmp_path / "lap2.csv"
    csv_file2.write_text("Speed,LapDistPct,Brake,Throttle\n105,0.5,0,1")

    second_lap = add_reference_lap_to_db(seeded_db, str(csv_file2), "Driver2", 144.5)

    # Refresh first lap to check its current state
    seeded_db.refresh(first_lap)

    # Verify first lap is now inactive
    assert first_lap.is_active is False

    # Verify second lap is active
    assert second_lap.is_active is True

    # Verify only the second lap is the active one in the database
    simulator = get_simulator_by_name(seeded_db, "iRacing")
    car = get_car_by_name(seeded_db, "Toyota GR86")
    track = get_track_by_name(seeded_db, "Spa")

    active_lap = get_active_reference_lap(seeded_db, simulator.id, car.id, track.id)
    assert active_lap is not None
    assert active_lap.id == second_lap.id
    assert active_lap.driver_name == "Driver2"
    assert active_lap.lap_time_seconds == 144.5
