"""Unit tests for analyze_lap_with_reference CLI script."""

from __future__ import annotations

import json

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scripts.analyze_lap_with_reference import build_parser, main
from src.db.models import Base
from src.db.repository import create_car, create_reference_lap, create_simulator, create_track


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()


def test_analyze_lap_with_reference_success(tmp_path, capsys, in_memory_db, monkeypatch):
    """Test successful execution with database reference."""
    # Create user CSV
    user_csv = tmp_path / "user.csv"
    user_data = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [180, 190, 200],
    })
    user_data.to_csv(user_csv, index=False)

    # Create reference CSV
    reference_csv = tmp_path / "reference.csv"
    reference_data = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [200, 200, 200],
    })
    reference_data.to_csv(reference_csv, index=False)

    # Setup database
    simulator = create_simulator(in_memory_db, name="iRacing")
    car = create_car(in_memory_db, name="Toyota GR86")
    track = create_track(in_memory_db, name="Spa")
    reference_lap = create_reference_lap(
        in_memory_db,
        simulator_id=simulator.id,
        car_id=car.id,
        track_id=track.id,
        csv_path=str(reference_csv),
        driver_name="Reference Driver",
        lap_time_seconds=120.0,
        is_active=True,
    )

    # Monkeypatch SessionLocal to use in-memory database
    monkeypatch.setattr("scripts.analyze_lap_with_reference.SessionLocal", lambda: in_memory_db)

    # Run script
    exit_code = main([
        str(user_csv),
        "--simulator", "iRacing",
        "--car", "Toyota GR86",
        "--track", "Spa",
    ])

    # Validate exit code
    assert exit_code == 0

    # Capture stdout
    captured = capsys.readouterr()
    stdout = captured.out

    # Validate stdout is valid JSON
    result = json.loads(stdout)

    # Validate structure
    assert "metadata" in result
    assert "comparison" in result
    assert "insights" in result


def test_analyze_lap_with_reference_simulator_not_found(capsys, in_memory_db, monkeypatch):
    """Test script with non-existent simulator."""
    # Monkeypatch SessionLocal to use in-memory database
    monkeypatch.setattr("scripts.analyze_lap_with_reference.SessionLocal", lambda: in_memory_db)

    # Run script with non-existent simulator
    exit_code = main([
        "user.csv",
        "--simulator", "NonExistentSim",
        "--car", "Toyota GR86",
        "--track", "Spa",
    ])

    # Validate exit code
    assert exit_code == 1

    # Capture stderr
    captured = capsys.readouterr()
    stderr = captured.err

    # Validate error message
    assert "simulator not found" in stderr


def test_analyze_lap_with_reference_car_not_found(capsys, in_memory_db, monkeypatch):
    """Test script with non-existent car."""
    # Setup database with simulator only
    simulator = create_simulator(in_memory_db, name="iRacing")

    # Monkeypatch SessionLocal to use in-memory database
    monkeypatch.setattr("scripts.analyze_lap_with_reference.SessionLocal", lambda: in_memory_db)

    # Run script with non-existent car
    exit_code = main([
        "user.csv",
        "--simulator", "iRacing",
        "--car", "NonExistentCar",
        "--track", "Spa",
    ])

    # Validate exit code
    assert exit_code == 1

    # Capture stderr
    captured = capsys.readouterr()
    stderr = captured.err

    # Validate error message
    assert "car not found" in stderr


def test_analyze_lap_with_reference_track_not_found(capsys, in_memory_db, monkeypatch):
    """Test script with non-existent track."""
    # Setup database with simulator and car
    simulator = create_simulator(in_memory_db, name="iRacing")
    car = create_car(in_memory_db, name="Toyota GR86")

    # Monkeypatch SessionLocal to use in-memory database
    monkeypatch.setattr("scripts.analyze_lap_with_reference.SessionLocal", lambda: in_memory_db)

    # Run script with non-existent track
    exit_code = main([
        "user.csv",
        "--simulator", "iRacing",
        "--car", "Toyota GR86",
        "--track", "NonExistentTrack",
    ])

    # Validate exit code
    assert exit_code == 1

    # Capture stderr
    captured = capsys.readouterr()
    stderr = captured.err

    # Validate error message
    assert "track not found" in stderr


def test_analyze_lap_with_reference_active_reference_not_found(capsys, in_memory_db, monkeypatch):
    """Test script when no active reference lap exists."""
    # Setup database with simulator, car, and track but no reference lap
    simulator = create_simulator(in_memory_db, name="iRacing")
    car = create_car(in_memory_db, name="Toyota GR86")
    track = create_track(in_memory_db, name="Spa")

    # Monkeypatch SessionLocal to use in-memory database
    monkeypatch.setattr("scripts.analyze_lap_with_reference.SessionLocal", lambda: in_memory_db)

    # Run script
    exit_code = main([
        "user.csv",
        "--simulator", "iRacing",
        "--car", "Toyota GR86",
        "--track", "Spa",
    ])

    # Validate exit code
    assert exit_code == 1

    # Capture stderr
    captured = capsys.readouterr()
    stderr = captured.err

    # Validate error message
    assert "active reference lap not found" in stderr


def test_analyze_lap_with_reference_user_csv_not_found(tmp_path, capsys, in_memory_db, monkeypatch):
    """Test script with non-existent user CSV."""
    # Create reference CSV
    reference_csv = tmp_path / "reference.csv"
    reference_data = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [200, 200, 200],
    })
    reference_data.to_csv(reference_csv, index=False)

    # Setup database
    simulator = create_simulator(in_memory_db, name="iRacing")
    car = create_car(in_memory_db, name="Toyota GR86")
    track = create_track(in_memory_db, name="Spa")
    reference_lap = create_reference_lap(
        in_memory_db,
        simulator_id=simulator.id,
        car_id=car.id,
        track_id=track.id,
        csv_path=str(reference_csv),
        driver_name="Reference Driver",
        lap_time_seconds=120.0,
        is_active=True,
    )

    # Monkeypatch SessionLocal to use in-memory database
    monkeypatch.setattr("scripts.analyze_lap_with_reference.SessionLocal", lambda: in_memory_db)

    # Run script with non-existent user CSV
    exit_code = main([
        "nonexistent_user.csv",
        "--simulator", "iRacing",
        "--car", "Toyota GR86",
        "--track", "Spa",
    ])

    # Validate exit code
    assert exit_code == 1

    # Capture stderr
    captured = capsys.readouterr()
    stderr = captured.err

    # Validate error message
    assert "user CSV file not found" in stderr


def test_analyze_lap_with_reference_custom_num_points(tmp_path, capsys, in_memory_db, monkeypatch):
    """Test script with custom num_points."""
    # Create user CSV
    user_csv = tmp_path / "user.csv"
    user_data = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [180, 190, 200],
    })
    user_data.to_csv(user_csv, index=False)

    # Create reference CSV
    reference_csv = tmp_path / "reference.csv"
    reference_data = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "speed": [200, 200, 200],
    })
    reference_data.to_csv(reference_csv, index=False)

    # Setup database
    simulator = create_simulator(in_memory_db, name="iRacing")
    car = create_car(in_memory_db, name="Toyota GR86")
    track = create_track(in_memory_db, name="Spa")
    reference_lap = create_reference_lap(
        in_memory_db,
        simulator_id=simulator.id,
        car_id=car.id,
        track_id=track.id,
        csv_path=str(reference_csv),
        driver_name="Reference Driver",
        lap_time_seconds=120.0,
        is_active=True,
    )

    # Monkeypatch SessionLocal to use in-memory database
    monkeypatch.setattr("scripts.analyze_lap_with_reference.SessionLocal", lambda: in_memory_db)

    # Run script with custom num_points
    exit_code = main([
        str(user_csv),
        "--simulator", "iRacing",
        "--car", "Toyota GR86",
        "--track", "Spa",
        "--num-points", "51",
    ])

    # Validate exit code
    assert exit_code == 0

    # Capture stdout
    captured = capsys.readouterr()
    stdout = captured.out

    # Parse JSON
    result = json.loads(stdout)

    # Validate num_points in metadata
    assert result["metadata"]["num_points"] == 51
    assert result["metadata"]["normalized_points"] == 51
