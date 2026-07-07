"""Repository functions for database CRUD operations."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from src.db.models import Car, ReferenceLap, Simulator, Track


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
