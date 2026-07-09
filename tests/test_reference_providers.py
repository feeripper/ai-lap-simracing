"""Tests for the reference lap provider layer (PR17)."""

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
)
from src.reference_providers.base import ReferenceLapCandidate
from src.reference_providers.exceptions import (
    ActiveReferenceLapNotFoundError,
    CarNotFoundError,
    SimulatorNotFoundError,
    TrackNotFoundError,
)
from src.reference_providers.garage61 import Garage61ReferenceLapProvider
from src.reference_providers.local import LocalReferenceLapProvider


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


def _seed_full(db_session, tmp_path, is_active=True):
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
        is_active=is_active,
    )
    return reference_csv


def test_local_provider_returns_active_reference(db_session, tmp_path):
    reference_csv = _seed_full(db_session, tmp_path)
    provider = LocalReferenceLapProvider(db_session)

    candidate = provider.find_reference_lap("iRacing", "Toyota GR86", "Spa")

    assert isinstance(candidate, ReferenceLapCandidate)
    assert candidate.source == "local"
    assert candidate.csv_path == str(reference_csv)
    assert candidate.driver_name == "Reference Driver"
    assert candidate.lap_time_seconds == 120.0
    assert candidate.simulator == "iRacing"
    assert provider.get_reference_csv_path(candidate) == str(reference_csv)


def test_local_provider_simulator_not_found(db_session):
    provider = LocalReferenceLapProvider(db_session)
    with pytest.raises(SimulatorNotFoundError):
        provider.find_reference_lap("iRacing", "Toyota GR86", "Spa")


def test_local_provider_car_not_found(db_session):
    create_simulator(db_session, name="iRacing")
    provider = LocalReferenceLapProvider(db_session)
    with pytest.raises(CarNotFoundError):
        provider.find_reference_lap("iRacing", "Toyota GR86", "Spa")


def test_local_provider_track_not_found(db_session):
    create_simulator(db_session, name="iRacing")
    create_car(db_session, name="Toyota GR86")
    provider = LocalReferenceLapProvider(db_session)
    with pytest.raises(TrackNotFoundError):
        provider.find_reference_lap("iRacing", "Toyota GR86", "Spa")


def test_local_provider_active_reference_not_found(db_session):
    create_simulator(db_session, name="iRacing")
    create_car(db_session, name="Toyota GR86")
    create_track(db_session, name="Spa")
    provider = LocalReferenceLapProvider(db_session)
    with pytest.raises(ActiveReferenceLapNotFoundError):
        provider.find_reference_lap("iRacing", "Toyota GR86", "Spa")


def test_garage61_provider_find_not_implemented():
    provider = Garage61ReferenceLapProvider()
    with pytest.raises(NotImplementedError):
        provider.find_reference_lap("iRacing", "Toyota GR86", "Spa")


def test_garage61_provider_get_csv_not_implemented():
    provider = Garage61ReferenceLapProvider()
    candidate = ReferenceLapCandidate(
        source="garage61",
        csv_path="unused.csv",
        driver_name="X",
        lap_time_seconds=100.0,
        simulator="iRacing",
        car="Toyota GR86",
        track="Spa",
    )
    with pytest.raises(NotImplementedError):
        provider.get_reference_csv_path(candidate)
