"""Repository functions for database CRUD operations."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from src.db.models import AnalysisRun, Car, ReferenceLap, Simulator, Track


def create_simulator(db: Session, name: str) -> Simulator:
    """Create a new simulator."""
    simulator = Simulator(name=name)
    db.add(simulator)
    db.commit()
    db.refresh(simulator)
    return simulator


def get_simulator_by_name(db: Session, name: str) -> Optional[Simulator]:
    """Get a simulator by name."""
    return db.query(Simulator).filter(Simulator.name == name).first()


def get_all_simulators(db: Session) -> list[Simulator]:
    """Get all simulators ordered by name."""
    return db.query(Simulator).order_by(Simulator.name).all()


def create_car(db: Session, name: str) -> Car:
    """Create a new car."""
    car = Car(name=name)
    db.add(car)
    db.commit()
    db.refresh(car)
    return car


def get_car_by_name(db: Session, name: str) -> Optional[Car]:
    """Get a car by name."""
    return db.query(Car).filter(Car.name == name).first()


def get_all_cars(db: Session) -> list[Car]:
    """Get all cars ordered by name."""
    return db.query(Car).order_by(Car.name).all()


def create_track(
    db: Session, name: str, layout: Optional[str] = None, corners_json: Optional[str] = None
) -> Track:
    """Create a new track."""
    track = Track(name=name, layout=layout, corners_json=corners_json)
    db.add(track)
    db.commit()
    db.refresh(track)
    return track


def get_track_by_name(db: Session, name: str) -> Optional[Track]:
    """Get a track by name."""
    return db.query(Track).filter(Track.name == name).first()


def get_all_tracks(db: Session) -> list[Track]:
    """Get all tracks ordered by name."""
    return db.query(Track).order_by(Track.name).all()


def create_reference_lap(
    db: Session,
    simulator_id: int,
    car_id: int,
    track_id: int,
    driver_name: str,
    lap_time_seconds: float,
    csv_path: str,
    is_active: bool = True,
) -> ReferenceLap:
    """Create a new reference lap. If is_active=True, deactivate any existing active lap for the same combination."""
    if is_active:
        # Deactivate any existing active reference lap for this combination
        db.query(ReferenceLap).filter(
            ReferenceLap.simulator_id == simulator_id,
            ReferenceLap.car_id == car_id,
            ReferenceLap.track_id == track_id,
            ReferenceLap.is_active == True,
        ).update({"is_active": False})

    reference_lap = ReferenceLap(
        simulator_id=simulator_id,
        car_id=car_id,
        track_id=track_id,
        driver_name=driver_name,
        lap_time_seconds=lap_time_seconds,
        csv_path=csv_path,
        is_active=is_active,
    )
    db.add(reference_lap)
    db.commit()
    db.refresh(reference_lap)
    return reference_lap


def get_active_reference_lap(
    db: Session, simulator_id: int, car_id: int, track_id: int
) -> Optional[ReferenceLap]:
    """Get the active reference lap for a given simulator, car, and track combination."""
    return (
        db.query(ReferenceLap)
        .filter(
            ReferenceLap.simulator_id == simulator_id,
            ReferenceLap.car_id == car_id,
            ReferenceLap.track_id == track_id,
            ReferenceLap.is_active == True,
        )
        .first()
    )


def get_all_reference_laps(
    db: Session, simulator_id: int, car_id: int, track_id: int
) -> list[ReferenceLap]:
    """Get all reference laps for a given simulator, car, and track combination."""
    return (
        db.query(ReferenceLap)
        .filter(
            ReferenceLap.simulator_id == simulator_id,
            ReferenceLap.car_id == car_id,
            ReferenceLap.track_id == track_id,
        )
        .all()
    )


def list_all_reference_laps(db: Session) -> list[ReferenceLap]:
    """List all reference laps across all combinations, ordered by id."""
    return db.query(ReferenceLap).order_by(ReferenceLap.id).all()


def create_analysis_run(
    db: Session,
    analysis_type: str,
    result_json: str,
    simulator_name: Optional[str] = None,
    car_name: Optional[str] = None,
    track_name: Optional[str] = None,
    user_csv_filename: Optional[str] = None,
    reference_csv_path: Optional[str] = None,
    summary: Optional[str] = None,
    priority: Optional[str] = None,
) -> AnalysisRun:
    """Persist an analysis run and return the created record."""
    analysis_run = AnalysisRun(
        analysis_type=analysis_type,
        result_json=result_json,
        simulator_name=simulator_name,
        car_name=car_name,
        track_name=track_name,
        user_csv_filename=user_csv_filename,
        reference_csv_path=reference_csv_path,
        summary=summary,
        priority=priority,
    )
    db.add(analysis_run)
    db.commit()
    db.refresh(analysis_run)
    return analysis_run


def get_analysis_run_by_id(db: Session, analysis_id: int) -> Optional[AnalysisRun]:
    """Get an analysis run by its id."""
    return db.query(AnalysisRun).filter(AnalysisRun.id == analysis_id).first()


def list_analysis_runs(db: Session) -> list[AnalysisRun]:
    """List all analysis runs ordered by most recent first."""
    return db.query(AnalysisRun).order_by(AnalysisRun.created_at.desc(), AnalysisRun.id.desc()).all()
