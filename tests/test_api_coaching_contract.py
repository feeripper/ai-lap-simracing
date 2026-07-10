"""Tests for the coaching contract and end-to-end backend flow."""

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
    """Create a TestClient with the db dependency overridden."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _make_user_csv(tmp_path):
    path = tmp_path / "user.csv"
    pd.DataFrame(
        {"lap_dist_pct": [0, 25, 50, 75, 100], "speed": [180, 170, 160, 175, 185]}
    ).to_csv(path, index=False)
    return path


def _make_reference_csv(tmp_path):
    path = tmp_path / "reference.csv"
    pd.DataFrame(
        {"lap_dist_pct": [0, 25, 50, 75, 100], "speed": [200, 190, 180, 195, 205]}
    ).to_csv(path, index=False)
    return path


def _seed_reference(db_session, tmp_path):
    simulator = create_simulator(db_session, name="iRacing")
    car = create_car(db_session, name="Toyota GR86")
    track = create_track(db_session, name="Spa-Francorchamps")
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


def test_analyze_returns_canonical_coaching_contract(client, tmp_path):
    """Test /analyze returns the canonical coaching response contract."""
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

    assert "analysis_id" in body
    assert "analysis_run_id" in body
    assert body["status"] == "completed"
    assert body["diagnosis_version"] == "1.0"
    assert isinstance(body["processing_time_ms"], (int, float))
    assert body["processing_time_ms"] >= 0
    assert "top_opportunities" in body
    assert "training_plan" in body
    assert "warnings" in body
    assert isinstance(body["top_opportunities"], list)
    assert len(body["top_opportunities"]) <= 3
    assert "primary_focus" in body["training_plan"]


def test_analyze_with_reference_returns_same_contract(client, db_session, tmp_path):
    """Test /analyze-with-reference returns the same canonical contract."""
    _seed_reference(db_session, tmp_path)
    user_csv = _make_user_csv(tmp_path)

    with user_csv.open("rb") as uf:
        response = client.post(
            "/analyze-with-reference",
            files={"user_csv": ("user.csv", uf, "text/csv")},
            data={
                "simulator": "iRacing",
                "car": "Toyota GR86",
                "track": "Spa-Francorchamps",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["diagnosis_version"] == "1.0"
    assert body["simulator"] == "iRacing"
    assert body["car"] == "Toyota GR86"
    assert body["track"] == "Spa-Francorchamps"
    assert "top_opportunities" in body
    assert "training_plan" in body


def test_get_analysis_by_id_preserves_coaching(client, tmp_path):
    """Test GET /analyses/{id} returns the same coaching content as creation."""
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

    assert post_response.status_code == 200
    post_body = post_response.json()
    analysis_id = post_body["analysis_id"]

    get_response = client.get(f"/analyses/{analysis_id}")
    assert get_response.status_code == 200
    get_body = get_response.json()

    assert get_body["analysis_id"] == analysis_id
    assert get_body["diagnosis_version"] == "1.0"
    assert get_body["top_opportunities"] == post_body["top_opportunities"]
    assert get_body["training_plan"] == post_body["training_plan"]


def test_list_analyses_returns_light_summary(client, tmp_path):
    """Test /analyses returns a lightweight summary without heavy telemetry."""
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
    summary = body[0]
    assert "analysis_id" in summary
    assert "id" in summary
    assert "analysis_type" in summary
    assert "number_of_opportunities" in summary
    assert "primary_focus" in summary
    assert "total_time_loss" in summary
    assert "comparison" not in summary
    assert "metadata" not in summary


def test_persistence_keeps_all_coaching_fields(client, db_session, tmp_path):
    """Test the persisted run contains all coaching fields."""
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
    runs = list_analysis_runs(db_session)
    assert len(runs) == 1
    result = runs[0].result_json
    assert "diagnosis_version" in result
    assert "processing_time_ms" in result
    assert "top_opportunities" in result
    assert "training_plan" in result
    assert "warnings" in result


def test_old_payload_remains_readable(client, db_session, tmp_path):
    """Test an old-style persisted result without new fields is readable."""
    import json

    from src.db.repository import create_analysis_run

    old_result = {
        "metadata": {},
        "comparison": {},
        "insights": {"summary": "old summary", "priority": "speed"},
        "diagnosis": {
            "overall_lap_delta_seconds": 1.0,
            "top_opportunities": [],
            "training_plan": {},
        },
    }
    old_run = create_analysis_run(
        db_session,
        analysis_type="direct_upload",
        result_json=json.dumps(old_result),
        summary="old summary",
        priority="speed",
    )

    response = client.get(f"/analyses/{old_run.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["analysis_id"] == old_run.id
    assert body["diagnosis_version"] == "1.0"
    assert body["status"] == "completed"
    assert body["top_opportunities"] == []
    assert body["training_plan"]["primary_focus"] is None
    assert body["training_plan"]["suggested_laps"] == 0
    assert body["training_plan"]["target_corners"] == []


def test_max_three_opportunities(client, tmp_path):
    """Test the response never contains more than 3 opportunities."""
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
    assert len(body["top_opportunities"]) <= 3


def test_opportunities_have_required_fields(client, tmp_path):
    """Test each opportunity contains the required fields."""
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
    for opp in body["top_opportunities"]:
        assert "rank" in opp
        assert "corner" in opp
        assert "phase" in opp
        assert "estimated_time_loss" in opp
        assert "confidence" in opp
        assert "probable_cause" in opp
        assert "recommendation" in opp
        assert opp["confidence"] in ["high", "medium", "low"]


def test_training_plan_consistent_when_no_opportunities(client, tmp_path):
    """Test training_plan is consistent when no opportunities are found."""
    user_csv = tmp_path / "user.csv"
    reference_csv = tmp_path / "reference.csv"
    # Equal data so no opportunities
    pd.DataFrame(
        {"lap_dist_pct": [0, 50, 100], "speed": [200, 200, 200]}
    ).to_csv(user_csv, index=False)
    pd.DataFrame(
        {"lap_dist_pct": [0, 50, 100], "speed": [200, 200, 200]}
    ).to_csv(reference_csv, index=False)

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
    assert body["top_opportunities"] == []
    assert body["training_plan"]["primary_focus"] is None
    assert body["training_plan"]["suggested_laps"] == 0
    assert body["training_plan"]["target_corners"] == []


def test_processing_time_ms_is_numeric(client, tmp_path):
    """Test processing_time_ms is numeric and non-negative."""
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
    assert isinstance(body["processing_time_ms"], (int, float))
    assert body["processing_time_ms"] >= 0


def test_processing_time_ms_not_prematurely_zero(client, tmp_path):
    """Test processing_time_ms preserves precision and is not rounded to zero."""
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
    assert body["processing_time_ms"] is not None
    assert body["processing_time_ms"] >= 0
    assert isinstance(body["processing_time_ms"], float)


def test_summary_uses_real_opportunity_count(client, tmp_path):
    """Test persisted summary uses the real number of opportunities and correct grammar."""
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
    opportunity_count = len(body["top_opportunities"])

    list_response = client.get("/analyses")
    assert list_response.status_code == 200
    summary = list_response.json()[0]["summary"]
    assert str(opportunity_count) in summary
    assert "recomenda" in summary


def test_unknown_cause_returns_low_confidence(client, tmp_path):
    """Test that unknown probable cause always returns low confidence."""
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
    for opp in body["top_opportunities"]:
        if opp["probable_cause"] == "unknown_or_low_confidence":
            assert opp["confidence"] == "low"


def test_unknown_recommendation_is_actionable(client, tmp_path):
    """Test unknown cause recommendation is not just compare telemetry."""
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
    for opp in body["top_opportunities"]:
        if opp["probable_cause"] == "unknown_or_low_confidence":
            assert "compare" not in opp["recommendation"].lower()
            assert "voltas" in opp["recommendation"].lower()


def test_secondary_focuses_no_duplicates(client, tmp_path):
    """Test training plan secondary_focuses has no duplicates and excludes primary."""
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
    plan = body["training_plan"]
    primary_focus = plan["primary_focus"]
    secondary_focuses = plan["secondary_focuses"]
    assert len(secondary_focuses) == len(set(secondary_focuses))
    assert primary_focus not in secondary_focuses


def test_training_plan_instructions_no_duplicates(client, tmp_path):
    """Test training plan instructions are not repeated."""
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
    instructions = body["training_plan"]["instructions"]
    assert len(instructions) == len(set(instructions))
