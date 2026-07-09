"""Local reference lap provider backed by the current database."""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.db.repository import (
    get_active_reference_lap,
    get_car_by_name,
    get_simulator_by_name,
    get_track_by_name,
)
from src.reference_providers.base import ReferenceLapCandidate
from src.reference_providers.exceptions import (
    ActiveReferenceLapNotFoundError,
    CarNotFoundError,
    SimulatorNotFoundError,
    TrackNotFoundError,
)

SOURCE_LOCAL = "local"


class LocalReferenceLapProvider:
    """Reference lap provider that reads the active reference lap from the database."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def find_reference_lap(
        self, simulator: str, car: str, track: str
    ) -> ReferenceLapCandidate:
        """Find the active reference lap for the given simulator, car, and track.

        Raises:
            SimulatorNotFoundError: If the simulator does not exist.
            CarNotFoundError: If the car does not exist.
            TrackNotFoundError: If the track does not exist.
            ActiveReferenceLapNotFoundError: If no active reference lap exists.
        """
        simulator_obj = get_simulator_by_name(self._db, simulator)
        if not simulator_obj:
            raise SimulatorNotFoundError(f"simulator not found: {simulator}")

        car_obj = get_car_by_name(self._db, car)
        if not car_obj:
            raise CarNotFoundError(f"car not found: {car}")

        track_obj = get_track_by_name(self._db, track)
        if not track_obj:
            raise TrackNotFoundError(f"track not found: {track}")

        reference_lap = get_active_reference_lap(
            self._db,
            simulator_id=simulator_obj.id,
            car_id=car_obj.id,
            track_id=track_obj.id,
        )
        if not reference_lap:
            raise ActiveReferenceLapNotFoundError(
                f"active reference lap not found for simulator '{simulator}', "
                f"car '{car}', track '{track}'"
            )

        return ReferenceLapCandidate(
            source=SOURCE_LOCAL,
            csv_path=reference_lap.csv_path,
            driver_name=reference_lap.driver_name,
            lap_time_seconds=reference_lap.lap_time_seconds,
            simulator=simulator,
            car=car,
            track=track,
            source_lap_id=str(reference_lap.id),
            source_url=None,
        )

    def get_reference_csv_path(self, reference_lap: ReferenceLapCandidate) -> str:
        """Return the CSV path of the given reference lap candidate."""
        return reference_lap.csv_path
