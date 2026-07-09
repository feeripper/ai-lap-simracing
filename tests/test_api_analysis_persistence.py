"""Tests for analysis persistence API endpoints (PR14)."""

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
    list_analysis_runs,
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


def _seed_reference(db_session, tmp_path):
    simulator = create_simulator(db_session, name="iRacing")
    car = create_car(db_session, name="Toyota GR86")
    track = create_track(db_session, name="Spa")
    reference_csv = _make_reference_csv(tmp_path)
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


def test_analyze_persists_run(client, db_session, tmp_path):
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
    assert "analysis_run_id" in body

    runs = list_analysis_runs(db_session)
    assert len(runs) == 1
    assert runs[0].analysis_type == "direct_upload"


def test_analyze_with_reference_persists_run(client, db_session, tmp_path):
    _seed_reference(db_session, tmp_path)
    user_csv = _make_user_csv(tmp_path)

    with user_csv.open("rb") as uf:
        response = client.post(
            "/analyze-with-reference",
            files={"user_csv": ("user.csv", uf, "text/csv")},
            data={"simulator": "iRacing", "car": "Toyota GR86", "track": "Spa"},
        )

    assert response.status_code == 200
    body = response.json()
    assert "analysis_run_id" in body

    runs = list_analysis_runs(db_session)
    assert len(runs) == 1
    assert runs[0].analysis_type == "active_reference"
    assert runs[0].simulator_name == "iRacing"


def test_list_analyses_returns_saved_item(client, db_session, tmp_path):
    user_csv = _make_user_csv(tmp_path)
    reference_csv = _make_reference_csv(tmp_path)

    with user_csv.open("rb") as uf, reference_csv.open("rb") as rf:
        client.post(
            "/analyze",
            files={
                "user_csv": ("user.csv", uf, "text/csv"),
                "reference_csv": ("reference.csv", rf, "text/csv"),
            },
        )

    response = client.get("/analyses")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["analysis_type"] == "direct_upload"
    assert "id" in body[0]
    assert "created_at" in body[0]


def test_get_analysis_by_id_returns_full(client, tmp_path):
    user_csv = _make_user_csv(tmp_path)
    reference_csv = _make_reference_csv(tmp_path)

    with user_csv.open("rb") as uf, reference_csv.open("rb") as rf:
        post_response = client.post(
            "/analyze",
            files={
                "user_csv": ("user.csv", uf, "text/csv"),
                "reference_csv": ("reference.csv", rf, "text/csv"),
            },
        )

    analysis_id = post_response.json()["analysis_run_id"]

    response = client.get(f"/analyses/{analysis_id}")
    assert response.status_code == 200
    body = response.json()
    assert "metadata" in body
    assert "comparison" in body
    assert "insights" in body
    assert body["analysis_run_id"] == analysis_id


def test_get_analysis_by_id_404(client):
    response = client.get("/analyses/99999")
    assert response.status_code == 404
