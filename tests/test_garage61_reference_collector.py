"""Tests for the Garage61 reference collector (no network access).

All Garage61 interactions are mocked via an injected fake client, so these tests never
touch the internet.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base
from src.db.repository import (
    create_car,
    create_reference_lap,
    create_simulator,
    create_track,
    get_active_reference_lap,
)
from src.reference_collectors.exceptions import (
    Garage61CandidateNotFoundError,
    Garage61CsvValidationError,
    Garage61DependencyMissingError,
    Garage61TokenMissingError,
)
from src.reference_collectors.garage61_collector import (
    Garage61ReferenceCollector,
    validate_reference_csv,
)
from src.reference_collectors.models import Garage61LapCandidate

VALID_CSV = "LapDistPct,Speed,Brake,Throttle\n0,200,0,1\n0.5,150,1,0\n1,210,0,1\n"
INVALID_CSV = "LapDistPct,Brake\n0,0\n0.5,1\n1,0\n"


class FakeGarage61Client:
    """In-memory stand-in for a Garage61 client used to avoid network calls in tests."""

    def __init__(self, candidates, csv_content):
        self._candidates = candidates
        self._csv_content = csv_content
        self.downloaded_ids: list[str] = []
        self.search_calls: list[dict] = []

    def search_laps(self, simulator, car, track, limit):
        self.search_calls.append(
            {"simulator": simulator, "car": car, "track": track, "limit": limit}
        )
        return list(self._candidates)[:limit]

    def download_csv(self, source_lap_id):
        self.downloaded_ids.append(source_lap_id)
        if isinstance(self._csv_content, dict):
            return self._csv_content.get(source_lap_id)
        return self._csv_content


def _candidate_dict(lap_id: str, lap_time: float) -> dict:
    return {
        "source_lap_id": lap_id,
        "driver_name": "Fast Driver",
        "lap_time_seconds": lap_time,
        "source_url": f"https://garage61.io/laps/{lap_id}",
        "track_layout": "GP",
        "extra_meta": "value",
    }


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


# -- token / dependency resolution ----------------------------------------------------


def test_token_missing_raises(monkeypatch):
    monkeypatch.delenv("GARAGE61_ACCESS_TOKEN", raising=False)
    collector = Garage61ReferenceCollector()
    with pytest.raises(Garage61TokenMissingError):
        collector.search_lap_candidates("iRacing", "Toyota GR86", "Spa")


def test_missing_optional_dependency_raises(monkeypatch):
    # Token present but no client injected -> tries to import the optional 'garage61'
    # dependency, which is not installed, so a clear error is raised.
    monkeypatch.setenv("GARAGE61_ACCESS_TOKEN", "fake-token")
    collector = Garage61ReferenceCollector()
    with pytest.raises(Garage61DependencyMissingError):
        collector.search_lap_candidates("iRacing", "Toyota GR86", "Spa")


# -- search / download -----------------------------------------------------------------


def test_search_lap_candidates_with_mock_client():
    client = FakeGarage61Client(
        candidates=[_candidate_dict("01ABC", 100.0), _candidate_dict("02DEF", 101.5)],
        csv_content=VALID_CSV,
    )
    collector = Garage61ReferenceCollector(client=client)

    candidates = collector.search_lap_candidates("iRacing", "Toyota GR86", "Spa", limit=5)

    assert len(candidates) == 2
    assert candidates[0].source == "garage61"
    assert candidates[0].source_lap_id == "01ABC"
    assert candidates[0].lap_time_seconds == 100.0
    assert candidates[0].source_url == "https://garage61.io/laps/01ABC"
    assert candidates[0].track_layout == "GP"
    assert candidates[0].raw_metadata["extra_meta"] == "value"
    assert client.search_calls[0]["limit"] == 5


def test_download_lap_csv_saves_file(tmp_path):
    client = FakeGarage61Client(candidates=[], csv_content=VALID_CSV)
    collector = Garage61ReferenceCollector(client=client)
    candidate = Garage61LapCandidate(
        source_lap_id="01ABC",
        driver_name="Fast Driver",
        lap_time_seconds=100.0,
        simulator="iRacing",
        car="Toyota GR86",
        track="Spa",
    )

    path = collector.download_lap_csv(candidate, tmp_path)

    assert path.exists()
    assert path.name == "garage61-01ABC.csv"
    assert candidate.csv_path == str(path)
    assert path.read_text(encoding="utf-8") == VALID_CSV


# -- CSV validation --------------------------------------------------------------------


def test_validate_valid_csv(tmp_path):
    csv_path = tmp_path / "valid.csv"
    csv_path.write_text(VALID_CSV, encoding="utf-8")
    # Should not raise.
    validate_reference_csv(csv_path)


def test_validate_invalid_csv_raises(tmp_path):
    csv_path = tmp_path / "invalid.csv"
    csv_path.write_text(INVALID_CSV, encoding="utf-8")
    with pytest.raises(Garage61CsvValidationError):
        validate_reference_csv(csv_path)


# -- full collection -------------------------------------------------------------------


def test_collect_reference_laps_creates_record(in_memory_db, tmp_path):
    client = FakeGarage61Client(
        candidates=[_candidate_dict("01ABC", 100.0)], csv_content=VALID_CSV
    )
    collector = Garage61ReferenceCollector(client=client, references_root=tmp_path)

    laps = collector.collect_reference_laps(
        in_memory_db, "iRacing", "Toyota GR86", "Spa"
    )

    assert len(laps) == 1
    lap = laps[0]
    assert lap.source == "garage61"
    assert lap.source_lap_id == "01ABC"
    assert lap.source_url == "https://garage61.io/laps/01ABC"
    assert lap.validation_status == "validated"
    assert lap.is_active is False
    assert lap.raw_metadata_json is not None


def test_collect_reference_laps_marks_invalid_as_rejected(in_memory_db, tmp_path):
    client = FakeGarage61Client(
        candidates=[_candidate_dict("BAD01", 100.0)], csv_content=INVALID_CSV
    )
    collector = Garage61ReferenceCollector(client=client, references_root=tmp_path)

    laps = collector.collect_reference_laps(
        in_memory_db, "iRacing", "Toyota GR86", "Spa"
    )

    assert len(laps) == 1
    assert laps[0].validation_status == "rejected"


def test_collect_reference_laps_no_duplicate(in_memory_db, tmp_path):
    client = FakeGarage61Client(
        candidates=[_candidate_dict("01ABC", 100.0)], csv_content=VALID_CSV
    )
    collector = Garage61ReferenceCollector(client=client, references_root=tmp_path)

    first = collector.collect_reference_laps(in_memory_db, "iRacing", "Toyota GR86", "Spa")
    second = collector.collect_reference_laps(in_memory_db, "iRacing", "Toyota GR86", "Spa")

    assert len(first) == 1
    assert len(second) == 1
    assert second[0].id == first[0].id

    from src.db.models import ReferenceLap

    all_laps = in_memory_db.query(ReferenceLap).all()
    assert len(all_laps) == 1


def test_collect_reference_laps_no_candidates_raises(in_memory_db, tmp_path):
    client = FakeGarage61Client(candidates=[], csv_content=VALID_CSV)
    collector = Garage61ReferenceCollector(client=client, references_root=tmp_path)

    with pytest.raises(Garage61CandidateNotFoundError):
        collector.collect_reference_laps(in_memory_db, "iRacing", "Toyota GR86", "Spa")


def test_collect_activate_best_true_activates_fastest_validated(in_memory_db, tmp_path):
    client = FakeGarage61Client(
        candidates=[_candidate_dict("SLOW", 105.0), _candidate_dict("FAST", 100.0)],
        csv_content=VALID_CSV,
    )
    collector = Garage61ReferenceCollector(client=client, references_root=tmp_path)

    laps = collector.collect_reference_laps(
        in_memory_db, "iRacing", "Toyota GR86", "Spa", activate_best=True
    )

    active = [lap for lap in laps if lap.is_active]
    assert len(active) == 1
    assert active[0].source_lap_id == "FAST"


def test_collect_activate_best_false_keeps_existing_active(in_memory_db, tmp_path):
    simulator = create_simulator(in_memory_db, "iRacing")
    car = create_car(in_memory_db, "Toyota GR86")
    track = create_track(in_memory_db, "Spa")

    manual = create_reference_lap(
        in_memory_db,
        simulator_id=simulator.id,
        car_id=car.id,
        track_id=track.id,
        driver_name="Manual Driver",
        lap_time_seconds=99.0,
        csv_path="/path/to/manual.csv",
        is_active=True,
    )

    client = FakeGarage61Client(
        candidates=[_candidate_dict("01ABC", 100.0)], csv_content=VALID_CSV
    )
    collector = Garage61ReferenceCollector(client=client, references_root=tmp_path)

    collected = collector.collect_reference_laps(
        in_memory_db, "iRacing", "Toyota GR86", "Spa", activate_best=False
    )

    in_memory_db.refresh(manual)
    assert manual.is_active is True
    assert all(lap.is_active is False for lap in collected)

    active = get_active_reference_lap(in_memory_db, simulator.id, car.id, track.id)
    assert active is not None
    assert active.id == manual.id
