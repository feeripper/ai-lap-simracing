"""Unit tests for database models and repository functions."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base, Car, ReferenceLap, Simulator, Track
from src.db.repository import (
    create_car,
    create_reference_lap,
    create_simulator,
    create_track,
    get_active_reference_lap,
    get_all_reference_laps,
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


def test_create_simulator(in_memory_db):
    """Test creating a simulator."""
    simulator = create_simulator(in_memory_db, "iRacing")
    assert simulator.id is not None
    assert simulator.name == "iRacing"


def test_get_simulator_by_name(in_memory_db):
    """Test retrieving a simulator by name."""
    create_simulator(in_memory_db, "iRacing")
    simulator = get_simulator_by_name(in_memory_db, "iRacing")
    assert simulator is not None
    assert simulator.name == "iRacing"


def test_get_simulator_by_name_not_found(in_memory_db):
    """Test retrieving a non-existent simulator."""
    simulator = get_simulator_by_name(in_memory_db, "NonExistent")
    assert simulator is None


def test_create_car(in_memory_db):
    """Test creating a car."""
    car = create_car(in_memory_db, "Toyota GR86")
    assert car.id is not None
    assert car.name == "Toyota GR86"


def test_get_car_by_name(in_memory_db):
    """Test retrieving a car by name."""
    create_car(in_memory_db, "Toyota GR86")
    car = get_car_by_name(in_memory_db, "Toyota GR86")
    assert car is not None
    assert car.name == "Toyota GR86"


def test_create_track(in_memory_db):
    """Test creating a track."""
    track = create_track(in_memory_db, "Spa", layout="GP", corners_json='{"corners": []}')
    assert track.id is not None
    assert track.name == "Spa"
    assert track.layout == "GP"
    assert track.corners_json == '{"corners": []}'


def test_create_track_without_optional_fields(in_memory_db):
    """Test creating a track without optional fields."""
    track = create_track(in_memory_db, "Spa")
    assert track.id is not None
    assert track.name == "Spa"
    assert track.layout is None
    assert track.corners_json is None


def test_get_track_by_name(in_memory_db):
    """Test retrieving a track by name."""
    create_track(in_memory_db, "Spa")
    track = get_track_by_name(in_memory_db, "Spa")
    assert track is not None
    assert track.name == "Spa"


def test_create_reference_lap(in_memory_db):
    """Test creating a reference lap."""
    simulator = create_simulator(in_memory_db, "iRacing")
    car = create_car(in_memory_db, "Toyota GR86")
    track = create_track(in_memory_db, "Spa")

    reference_lap = create_reference_lap(
        in_memory_db,
        simulator_id=simulator.id,
        car_id=car.id,
        track_id=track.id,
        driver_name="FastDriver",
        lap_time_seconds=145.234,
        csv_path="/path/to/lap.csv",
        is_active=True,
    )

    assert reference_lap.id is not None
    assert reference_lap.driver_name == "FastDriver"
    assert reference_lap.lap_time_seconds == 145.234
    assert reference_lap.csv_path == "/path/to/lap.csv"
    assert reference_lap.is_active is True


def test_get_active_reference_lap(in_memory_db):
    """Test retrieving the active reference lap."""
    simulator = create_simulator(in_memory_db, "iRacing")
    car = create_car(in_memory_db, "Toyota GR86")
    track = create_track(in_memory_db, "Spa")

    # Create an active reference lap
    active_lap = create_reference_lap(
        in_memory_db,
        simulator_id=simulator.id,
        car_id=car.id,
        track_id=track.id,
        driver_name="FastDriver",
        lap_time_seconds=145.234,
        csv_path="/path/to/active.csv",
        is_active=True,
    )

    # Create an inactive reference lap
    create_reference_lap(
        in_memory_db,
        simulator_id=simulator.id,
        car_id=car.id,
        track_id=track.id,
        driver_name="SlowDriver",
        lap_time_seconds=150.0,
        csv_path="/path/to/inactive.csv",
        is_active=False,
    )

    retrieved = get_active_reference_lap(in_memory_db, simulator.id, car.id, track.id)
    assert retrieved is not None
    assert retrieved.id == active_lap.id
    assert retrieved.is_active is True


def test_get_active_reference_lap_not_found(in_memory_db):
    """Test retrieving an active reference lap when none exists."""
    simulator = create_simulator(in_memory_db, "iRacing")
    car = create_car(in_memory_db, "Toyota GR86")
    track = create_track(in_memory_db, "Spa")

    retrieved = get_active_reference_lap(in_memory_db, simulator.id, car.id, track.id)
    assert retrieved is None


def test_get_all_reference_laps(in_memory_db):
    """Test retrieving all reference laps for a combination."""
    simulator = create_simulator(in_memory_db, "iRacing")
    car = create_car(in_memory_db, "Toyota GR86")
    track = create_track(in_memory_db, "Spa")

    # Create multiple reference laps
    create_reference_lap(
        in_memory_db,
        simulator_id=simulator.id,
        car_id=car.id,
        track_id=track.id,
        driver_name="Driver1",
        lap_time_seconds=145.0,
        csv_path="/path/to/lap1.csv",
    )
    create_reference_lap(
        in_memory_db,
        simulator_id=simulator.id,
        car_id=car.id,
        track_id=track.id,
        driver_name="Driver2",
        lap_time_seconds=146.0,
        csv_path="/path/to/lap2.csv",
    )

    all_laps = get_all_reference_laps(in_memory_db, simulator.id, car.id, track.id)
    assert len(all_laps) == 2


def test_unique_constraint_simulator_name(in_memory_db):
    """Test that simulator names are unique."""
    create_simulator(in_memory_db, "iRacing")
    with pytest.raises(Exception):  # SQLAlchemy will raise an integrity error
        create_simulator(in_memory_db, "iRacing")


def test_unique_constraint_car_name(in_memory_db):
    """Test that car names are unique."""
    create_car(in_memory_db, "Toyota GR86")
    with pytest.raises(Exception):
        create_car(in_memory_db, "Toyota GR86")


def test_unique_constraint_track_name(in_memory_db):
    """Test that track names are unique."""
    create_track(in_memory_db, "Spa")
    with pytest.raises(Exception):
        create_track(in_memory_db, "Spa")


def test_create_reference_lap_deactivates_existing_active(in_memory_db):
    """Test that creating a new active reference lap deactivates the previous one."""
    simulator = create_simulator(in_memory_db, "iRacing")
    car = create_car(in_memory_db, "Toyota GR86")
    track = create_track(in_memory_db, "Spa")

    # Create first active reference lap
    first_lap = create_reference_lap(
        in_memory_db,
        simulator_id=simulator.id,
        car_id=car.id,
        track_id=track.id,
        driver_name="Driver1",
        lap_time_seconds=145.0,
        csv_path="/path/to/lap1.csv",
        is_active=True,
    )

    # Create second active reference lap for the same combination
    second_lap = create_reference_lap(
        in_memory_db,
        simulator_id=simulator.id,
        car_id=car.id,
        track_id=track.id,
        driver_name="Driver2",
        lap_time_seconds=144.5,
        csv_path="/path/to/lap2.csv",
        is_active=True,
    )

    # Refresh first lap from database to check its current state
    in_memory_db.refresh(first_lap)

    # Verify first lap is now inactive
    assert first_lap.is_active is False

    # Verify second lap is active
    assert second_lap.is_active is True

    # Verify get_active_reference_lap returns the second lap
    active = get_active_reference_lap(in_memory_db, simulator.id, car.id, track.id)
    assert active is not None
    assert active.id == second_lap.id
    assert active.driver_name == "Driver2"
