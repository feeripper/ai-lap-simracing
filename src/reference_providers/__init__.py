"""Reference lap provider layer.

This package abstracts the source of reference laps so the analysis core stays
generic. The local provider uses the current database; the Garage61 provider is a
stub for future integration (see the Garage61 spike documentation).
"""

from src.reference_providers.base import ReferenceLapCandidate, ReferenceLapProvider
from src.reference_providers.exceptions import (
    ActiveReferenceLapNotFoundError,
    CarNotFoundError,
    ReferenceProviderError,
    SimulatorNotFoundError,
    TrackNotFoundError,
)
from src.reference_providers.garage61 import Garage61ReferenceLapProvider
from src.reference_providers.local import LocalReferenceLapProvider

__all__ = [
    "ReferenceLapCandidate",
    "ReferenceLapProvider",
    "ReferenceProviderError",
    "SimulatorNotFoundError",
    "CarNotFoundError",
    "TrackNotFoundError",
    "ActiveReferenceLapNotFoundError",
    "LocalReferenceLapProvider",
    "Garage61ReferenceLapProvider",
]
