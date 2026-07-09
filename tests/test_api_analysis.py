"""Tests for the analysis API endpoints (PR12)."""

from __future__ import annotations

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_db
from src.api.main import app
from src.db.models import Base
from src.db.repository import (
    create_car,
    create_reference_lap,
    create_simulator,
    create_track,
)


@pytest.fixture
def db_session(tmp_path):
    """Create a file-based SQLite database session for testing.

    A file-based database (instead of ':memory:') is used because the API
    endpoint and the test each open their own session; an in-memory SQLite
    database is not shared across separate connections/threads.
    """
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def client(db_session):
    """Create a TestClient with the db dependency overridden."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _make_user_csv(tmp_path):
    path = tmp_path / "user.csv"
    pd.DataFrame(
        {"lap_dist_pct": [0, 50, 100], "speed": [180, 190, 200]}
    ).to_csv(path, index=False)
    return path


def _make_reference_csv(tmp_path):
    path = tmp_path / "reference.csv"
    pd.DataFrame(
        {"lap_dist_pct": [0, 50, 100], "speed": [200, 200, 200]}
    ).to_csv(path, index=False)
    return path


def test_catalog_returns_200(client):
    response = client.get("/catalog")
    assert response.status_code == 200
    body = response.json()
    assert "simulators" in body
    assert "cars" in body
    assert "tracks" in body


def test_analyze_with_two_valid_csvs(client, tmp_path):
    user_csv = _make_user_csv(tmp_path)
    reference_csv = _make_reference_csv(tmp_path)

    with user_csv.open("rb") as uf, reference_csv.open("rb") as rf:
        response = client.post(
            "/analyze",
            files={
                "user_csv": ("user.csv", uf, "text/csv"),
                "reference_csv": ("reference.csv", rf, "text/csv"),
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert "metadata" in body
    assert "comparison" in body
    assert "insights" in body


def test_analyze_rejects_non_csv(client, tmp_path):
    bad_file = tmp_path / "user.txt"
    bad_file.write_text("not a csv")
    reference_csv = _make_reference_csv(tmp_path)

    with bad_file.open("rb") as uf, reference_csv.open("rb") as rf:
        response = client.post(
            "/analyze",
            files={
                "user_csv": ("user.txt", uf, "text/plain"),
                "reference_csv": ("reference.csv", rf, "text/csv"),
            },
        )

    assert response.status_code == 400


def test_analyze_with_reference_404_when_no_active_reference(client, db_session, tmp_path):
    user_csv = _make_user_csv(tmp_path)

    # Create simulator/car/track, but no reference lap, so the endpoint
    # should fail specifically on "active reference lap not found".
    create_simulator(db_session, name="iRacing")
    create_car(db_session, name="Toyota GR86")
    create_track(db_session, name="Spa")

    with user_csv.open("rb") as uf:
        response = client.post(
            "/analyze-with-reference",
            files={"user_csv": ("user.csv", uf, "text/csv")},
            data={
                "simulator": "iRacing",
                "car": "Toyota GR86",
                "track": "Spa",
            },
        )

    assert response.status_code == 404
    assert "active reference lap not found" in response.json()["detail"]


def test_analyze_with_reference_success(client, db_session, tmp_path):
    user_csv = _make_user_csv(tmp_path)
    reference_csv = _make_reference_csv(tmp_path)

    simulator = create_simulator(db_session, name="iRacing")
    car = create_car(db_session, name="Toyota GR86")
    track = create_track(db_session, name="Spa")
    create_reference_lap(
        db_session,
        simulator_id=simulator.id,
        car_id=car.id,
        track_id=track.id,
        driver_name="Reference Driver",
        lap_time_seconds=120.0,
        csv_path=str(reference_csv),
        is_active=True,
    )

    with user_csv.open("rb") as uf:
        response = client.post(
            "/analyze-with-reference",
            files={"user_csv": ("user.csv", uf, "text/csv")},
            data={
                "simulator": "iRacing",
                "car": "Toyota GR86",
                "track": "Spa",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert "metadata" in body
    assert "comparison" in body
    assert "insights" in body
