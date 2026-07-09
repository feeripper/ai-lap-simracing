"""Exceptions for the reference collector layer."""

from __future__ import annotations


class ReferenceCollectorError(Exception):
    """Base exception for reference collector errors."""


class Garage61TokenMissingError(ReferenceCollectorError):
    """Raised when a Garage61 access token is required but not configured.

    The collector reads the token from the constructor argument or, as a fallback, from
    the ``GARAGE61_ACCESS_TOKEN`` environment variable.
    """


class Garage61DependencyMissingError(ReferenceCollectorError):
    """Raised when the optional Garage61 client dependency is not installed.

    External Garage61 dependencies are imported lazily/optionally so that importing this
    package never forces the dependency to be installed. This error is raised only when a
    method that actually needs the dependency is called.
    """


class Garage61CandidateNotFoundError(ReferenceCollectorError):
    """Raised when no lap candidates are found for the requested combination."""


class Garage61CsvDownloadError(ReferenceCollectorError):
    """Raised when a candidate's telemetry CSV cannot be downloaded."""


class Garage61CsvValidationError(ReferenceCollectorError):
    """Raised when a downloaded CSV does not meet the minimum telemetry requirements."""
