"""Tests for the catalog API endpoints (PR13)."""

from __future__ import annotations

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
    """Create a file-based SQLite database session for testing."""
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


def _seed(db_session, tmp_path):
    simulator = create_simulator(db_session, name="iRacing")
    car = create_car(db_session, name="Toyota GR86")
    track = create_track(db_session, name="Spa")
    reference_csv = tmp_path / "reference.csv"
    reference_csv.write_text("lap_dist_pct,speed\n0,200\n")
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


def test_simulators_empty(client):
    response = client.get("/simulators")
    assert response.status_code == 200
    assert response.json() == []


def test_cars_empty(client):
    response = client.get("/cars")
    assert response.status_code == 200
    assert response.json() == []


def test_tracks_empty(client):
    response = client.get("/tracks")
    assert response.status_code == 200
    assert response.json() == []


def test_catalog_empty(client):
    response = client.get("/catalog")
    assert response.status_code == 200
    body = response.json()
    assert body == {"simulators": [], "cars": [], "tracks": []}


def test_simulators_with_seed(client, db_session, tmp_path):
    _seed(db_session, tmp_path)
    response = client.get("/simulators")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "iRacing"
    assert "id" in body[0]


def test_cars_with_seed(client, db_session, tmp_path):
    _seed(db_session, tmp_path)
    response = client.get("/cars")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Toyota GR86"


def test_tracks_with_seed(client, db_session, tmp_path):
    _seed(db_session, tmp_path)
    response = client.get("/tracks")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Spa"


def test_catalog_with_seed(client, db_session, tmp_path):
    _seed(db_session, tmp_path)
    response = client.get("/catalog")
    assert response.status_code == 200
    body = response.json()
    assert [s["name"] for s in body["simulators"]] == ["iRacing"]
    assert [c["name"] for c in body["cars"]] == ["Toyota GR86"]
    assert [t["name"] for t in body["tracks"]] == ["Spa"]


def test_reference_laps_with_seed(client, db_session, tmp_path):
    _seed(db_session, tmp_path)
    response = client.get("/reference-laps")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    lap = body[0]
    assert lap["driver_name"] == "Reference Driver"
    assert lap["simulator"] == "iRacing"
    assert lap["car"] == "Toyota GR86"
    assert lap["track"] == "Spa"
    assert lap["is_active"] is True
    assert lap["source"] == "manual"
    assert lap["validation_status"] == "validated"
    assert lap["source_lap_id"] is None
