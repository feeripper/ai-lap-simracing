"""Tests for the sync_reference_laps CLI helper (no network access)."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scripts.sync_reference_laps import run_sync
from src.db.models import Base
from src.reference_collectors.exceptions import Garage61TokenMissingError
from src.reference_collectors.garage61_collector import Garage61ReferenceCollector

VALID_CSV = "LapDistPct,Speed,Brake,Throttle\n0,200,0,1\n0.5,150,1,0\n1,210,0,1\n"


class FakeGarage61Client:
    def __init__(self, candidates, csv_content):
        self._candidates = candidates
        self._csv_content = csv_content

    def search_laps(self, simulator, car, track, limit):
        return list(self._candidates)[:limit]

    def download_csv(self, source_lap_id):
        return self._csv_content


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


def test_run_sync_collects_with_injected_collector(in_memory_db, tmp_path):
    client = FakeGarage61Client(
        candidates=[
            {
                "source_lap_id": "01ABC",
                "driver_name": "Fast Driver",
                "lap_time_seconds": 100.0,
                "source_url": "https://garage61.io/laps/01ABC",
            }
        ],
        csv_content=VALID_CSV,
    )
    collector = Garage61ReferenceCollector(client=client, references_root=tmp_path)

    laps = run_sync(
        in_memory_db,
        simulator="iRacing",
        car="Toyota GR86",
        track="Spa",
        collector=collector,
    )

    assert len(laps) == 1
    assert laps[0].source == "garage61"
    assert laps[0].source_lap_id == "01ABC"


def test_run_sync_without_token_raises(monkeypatch, in_memory_db):
    monkeypatch.delenv("GARAGE61_ACCESS_TOKEN", raising=False)
    with pytest.raises(Garage61TokenMissingError):
        run_sync(in_memory_db, simulator="iRacing", car="Toyota GR86", track="Spa")
