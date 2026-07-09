"""Exceptions for the reference lap provider layer."""

from __future__ import annotations


class ReferenceProviderError(Exception):
    """Base exception for reference lap provider errors."""


class SimulatorNotFoundError(ReferenceProviderError):
    """Raised when the requested simulator is not found."""


class CarNotFoundError(ReferenceProviderError):
    """Raised when the requested car is not found."""


class TrackNotFoundError(ReferenceProviderError):
    """Raised when the requested track is not found."""


class ActiveReferenceLapNotFoundError(ReferenceProviderError):
    """Raised when no active reference lap exists for the requested combination."""
