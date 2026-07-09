"""Reference collectors layer.

This package populates the database with reference laps fetched from external,
experimental sources (e.g. Garage61). It is intentionally decoupled from the analysis
pipeline and from the reference *provider* layer:

- Providers (``src/reference_providers/``) read reference laps that already exist.
- Collectors (this package) fetch candidate laps from external sources, download and
  validate their telemetry CSVs, cache them locally, and persist them as ``ReferenceLap``
  records.

External dependencies (e.g. a Garage61 client library) are imported optionally and only
when needed, so importing this package never requires the external dependency to be
installed.
"""

from __future__ import annotations

from src.reference_collectors.exceptions import (
    Garage61CandidateNotFoundError,
    Garage61CsvDownloadError,
    Garage61CsvValidationError,
    Garage61DependencyMissingError,
    Garage61TokenMissingError,
    ReferenceCollectorError,
)
from src.reference_collectors.garage61_collector import (
    Garage61ReferenceCollector,
    slugify,
    validate_reference_csv,
)
from src.reference_collectors.models import Garage61LapCandidate

__all__ = [
    "Garage61LapCandidate",
    "Garage61ReferenceCollector",
    "slugify",
    "validate_reference_csv",
    "ReferenceCollectorError",
    "Garage61TokenMissingError",
    "Garage61DependencyMissingError",
    "Garage61CandidateNotFoundError",
    "Garage61CsvDownloadError",
    "Garage61CsvValidationError",
]
