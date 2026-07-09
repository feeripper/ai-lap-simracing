"""Garage61 reference lap collector (experimental spike).

This module fetches candidate reference laps from Garage61, downloads their telemetry
CSVs, validates them, caches them locally, and persists them as ``ReferenceLap`` records.

Design constraints (see docs-site/docs/garage61-spike.md):

- Garage61 is an *optional, experimental* external source. Nothing in the main analysis
  flow depends on it.
- Any Garage61 client dependency is imported lazily/optionally. Importing this module
  never requires that dependency to be installed.
- No HTML scraping, no browser automation, no auth bypass.
- Tests must never hit the network: inject a mock ``client`` into the collector.
- Collected laps are never auto-activated unless explicitly requested.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from sqlalchemy.orm import Session

from src.analysis.telemetry_columns import standardize_telemetry_columns
from src.db.models import ReferenceLap
from src.db.repository import (
    activate_reference_lap,
    create_car,
    create_reference_lap,
    create_simulator,
    create_track,
    get_car_by_name,
    get_reference_lap_by_source_id,
    get_simulator_by_name,
    get_track_by_name,
)
from src.reference_collectors.exceptions import (
    Garage61CandidateNotFoundError,
    Garage61CsvDownloadError,
    Garage61CsvValidationError,
    Garage61DependencyMissingError,
    Garage61TokenMissingError,
)
from src.reference_collectors.models import SOURCE_GARAGE61, Garage61LapCandidate

TOKEN_ENV_VAR = "GARAGE61_ACCESS_TOKEN"
DEFAULT_REFERENCES_ROOT = Path("data/references")

VALIDATION_VALIDATED = "validated"
VALIDATION_REJECTED = "rejected"

# Minimum standardized columns required for a reference CSV to be usable by the pipeline.
_REQUIRED_DISTANCE_COLUMN = "lap_dist_pct"
_REQUIRED_SPEED_COLUMN = "speed"


def slugify(value: str) -> str:
    """Return a filesystem-friendly slug for a name (e.g. 'Toyota GR86' -> 'toyota-gr86')."""
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "unknown"


def validate_reference_csv(csv_path: str | Path) -> None:
    """Validate a downloaded reference CSV using the shared telemetry standardization.

    Accepts both Garage61 exports (e.g. ``LapDistPct``, ``Speed``) and the internal format
    (``lap_dist_pct``, ``speed``). Requires at least a compatible distance column and a
    compatible speed column.

    Raises:
        Garage61CsvValidationError: If the CSV cannot be read or is missing required columns.
    """
    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:  # noqa: BLE001 - surface any read error as a validation error
        raise Garage61CsvValidationError(f"could not read CSV '{csv_path}': {exc}") from exc

    if df.empty:
        raise Garage61CsvValidationError(f"CSV '{csv_path}' is empty")

    standardized = standardize_telemetry_columns(df)
    columns = set(standardized.columns)

    if _REQUIRED_DISTANCE_COLUMN not in columns:
        raise Garage61CsvValidationError(
            f"CSV '{csv_path}' is missing a compatible distance column "
            f"(expected one that maps to '{_REQUIRED_DISTANCE_COLUMN}')"
        )
    if _REQUIRED_SPEED_COLUMN not in columns:
        raise Garage61CsvValidationError(
            f"CSV '{csv_path}' is missing a compatible speed column "
            f"(expected one that maps to '{_REQUIRED_SPEED_COLUMN}')"
        )


class Garage61ReferenceCollector:
    """Collect reference laps from Garage61 into the local database.

    The collector is safe to construct without a token or the optional dependency; those
    are only required when a method that actually talks to Garage61 is called. For tests,
    pass a mock ``client`` to bypass token/dependency resolution entirely.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        client: Any = None,
        references_root: str | Path | None = None,
    ) -> None:
        self._token = token or os.environ.get(TOKEN_ENV_VAR) or None
        self._client = client
        self._references_root = (
            Path(references_root) if references_root is not None else DEFAULT_REFERENCES_ROOT
        )

    # -- client resolution -------------------------------------------------------------

    def _get_client(self) -> Any:
        """Return the Garage61 client, resolving token and optional dependency as needed.

        Raises:
            Garage61TokenMissingError: If no token is configured (arg or env var).
            Garage61DependencyMissingError: If the optional Garage61 dependency is missing.
        """
        if self._client is not None:
            return self._client

        if not self._token:
            raise Garage61TokenMissingError(
                f"Garage61 access token is not configured. Set the {TOKEN_ENV_VAR} "
                "environment variable or pass token=... to the collector."
            )

        self._client = self._build_client()
        return self._client

    def _build_client(self) -> Any:
        """Build a Garage61 client from the optional dependency.

        Raises:
            Garage61DependencyMissingError: If the dependency is not installed or does not
                expose a usable client class.
        """
        try:
            import garage61  # type: ignore
        except ImportError as exc:
            raise Garage61DependencyMissingError(
                "The optional 'garage61' dependency is not installed. Install it to enable "
                "automatic reference lap collection, or provide a client explicitly."
            ) from exc

        client_factory = getattr(garage61, "Client", None) or getattr(
            garage61, "Garage61Client", None
        )
        if client_factory is None:
            raise Garage61DependencyMissingError(
                "The 'garage61' dependency does not expose a 'Client' or 'Garage61Client' class."
            )
        return client_factory(token=self._token)

    # -- candidate discovery -----------------------------------------------------------

    def search_lap_candidates(
        self, simulator: str, car: str, track: str, limit: int = 5
    ) -> list[Garage61LapCandidate]:
        """Search Garage61 for candidate reference laps for the given combination.

        Returns a (possibly empty) list of candidates. Network access happens only through
        the injected/resolved client, so this is fully mockable in tests.
        """
        client = self._get_client()
        raw_results = client.search_laps(
            simulator=simulator, car=car, track=track, limit=limit
        )
        return [
            self._parse_candidate(item, simulator, car, track) for item in (raw_results or [])
        ]

    @staticmethod
    def _parse_candidate(
        item: Any, simulator: str, car: str, track: str
    ) -> Garage61LapCandidate:
        """Defensively parse a raw client result (dict or object) into a candidate."""
        if isinstance(item, dict):
            def get(key: str, default: Any = None) -> Any:
                return item.get(key, default)

            raw_metadata = dict(item)
        else:
            def get(key: str, default: Any = None) -> Any:
                return getattr(item, key, default)

            raw_metadata = {}

        source_lap_id = get("source_lap_id") or get("lap_id") or get("id")
        if source_lap_id is None:
            raise Garage61CandidateNotFoundError(
                "Garage61 result is missing a lap id (expected 'source_lap_id', 'lap_id', or 'id')."
            )

        lap_time = get("lap_time_seconds")
        if lap_time is None:
            lap_time = get("lap_time")

        return Garage61LapCandidate(
            source_lap_id=str(source_lap_id),
            driver_name=str(get("driver_name") or get("driver") or "unknown"),
            lap_time_seconds=float(lap_time) if lap_time is not None else 0.0,
            simulator=simulator,
            car=car,
            track=track,
            source=SOURCE_GARAGE61,
            source_url=get("source_url") or get("url"),
            track_layout=get("track_layout") or get("layout"),
            raw_metadata=raw_metadata,
        )

    # -- CSV download ------------------------------------------------------------------

    def download_lap_csv(
        self, candidate: Garage61LapCandidate, destination_dir: str | Path
    ) -> Path:
        """Download a candidate's telemetry CSV and save it under ``destination_dir``.

        The file is named ``garage61-<source_lap_id>.csv``.

        Raises:
            Garage61CsvDownloadError: If the client returns no usable CSV content.
        """
        client = self._get_client()
        content = client.download_csv(candidate.source_lap_id)

        if content is None:
            raise Garage61CsvDownloadError(
                f"Garage61 returned no CSV content for lap '{candidate.source_lap_id}'."
            )
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        if not content.strip():
            raise Garage61CsvDownloadError(
                f"Garage61 returned empty CSV content for lap '{candidate.source_lap_id}'."
            )

        destination = Path(destination_dir)
        destination.mkdir(parents=True, exist_ok=True)
        csv_path = destination / f"garage61-{candidate.source_lap_id}.csv"
        csv_path.write_text(content, encoding="utf-8")

        candidate.csv_path = str(csv_path)
        return csv_path

    # -- full collection ---------------------------------------------------------------

    def collect_reference_laps(
        self,
        db: Session,
        simulator: str,
        car: str,
        track: str,
        limit: int = 5,
        activate_best: bool = False,
    ) -> list[ReferenceLap]:
        """Search, download, validate, and persist Garage61 reference laps.

        Behavior:
            - Existing laps (same source + source_lap_id) are reused, never duplicated.
            - Newly collected laps are created inactive with validation_status
              "validated" or "rejected".
            - The current active reference lap is left untouched unless ``activate_best``
              is True, in which case the fastest *validated* collected lap is activated.

        Raises:
            Garage61CandidateNotFoundError: If no candidates are found.
        """
        candidates = self.search_lap_candidates(simulator, car, track, limit=limit)
        if not candidates:
            raise Garage61CandidateNotFoundError(
                f"No Garage61 lap candidates found for simulator '{simulator}', "
                f"car '{car}', track '{track}'."
            )

        simulator_obj = get_simulator_by_name(db, simulator) or create_simulator(db, simulator)
        car_obj = get_car_by_name(db, car) or create_car(db, car)
        track_obj = get_track_by_name(db, track) or create_track(db, track)

        destination_dir = (
            self._references_root / slugify(simulator) / slugify(car) / slugify(track)
        )

        collected: list[ReferenceLap] = []
        for candidate in candidates:
            existing = get_reference_lap_by_source_id(
                db, candidate.source, candidate.source_lap_id
            )
            if existing is not None:
                collected.append(existing)
                continue

            csv_path = self.download_lap_csv(candidate, destination_dir)

            try:
                validate_reference_csv(csv_path)
                validation_status = VALIDATION_VALIDATED
            except Garage61CsvValidationError:
                validation_status = VALIDATION_REJECTED

            raw_metadata_json = (
                json.dumps(candidate.raw_metadata) if candidate.raw_metadata else None
            )

            reference_lap = create_reference_lap(
                db,
                simulator_id=simulator_obj.id,
                car_id=car_obj.id,
                track_id=track_obj.id,
                driver_name=candidate.driver_name,
                lap_time_seconds=candidate.lap_time_seconds,
                csv_path=str(csv_path),
                is_active=False,
                source=candidate.source,
                source_lap_id=candidate.source_lap_id,
                source_url=candidate.source_url,
                track_layout=candidate.track_layout,
                validation_status=validation_status,
                raw_metadata_json=raw_metadata_json,
            )
            collected.append(reference_lap)

        if activate_best:
            self._activate_best_validated(db, collected)

        return collected

    @staticmethod
    def _activate_best_validated(
        db: Session, reference_laps: list[ReferenceLap]
    ) -> Optional[ReferenceLap]:
        """Activate the fastest validated reference lap, if any."""
        validated = [
            lap for lap in reference_laps if lap.validation_status == VALIDATION_VALIDATED
        ]
        if not validated:
            return None
        best = min(validated, key=lambda lap: lap.lap_time_seconds)
        return activate_reference_lap(db, best.id)
