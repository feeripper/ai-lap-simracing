"""Stub Garage61 reference lap provider.

This is a placeholder for the future Garage61 integration. It is intentionally not
implemented: the concrete implementation depends on the outcome of the Garage61 spike
(see docs-site/docs/garage61-spike.md). This class must NOT be used in production yet.
"""

from __future__ import annotations

from src.reference_providers.base import ReferenceLapCandidate

_NOT_IMPLEMENTED_MESSAGE = (
    "Garage61ReferenceLapProvider is not implemented yet. Its implementation depends "
    "on the Garage61 spike (see docs-site/docs/garage61-spike.md). Use "
    "LocalReferenceLapProvider for now."
)


class Garage61ReferenceLapProvider:
    """Future provider that will fetch reference laps from Garage61.

    All methods currently raise NotImplementedError. The real implementation will
    depend on confirming API availability, authentication, filtering by car/track,
    ordering by best time, CSV export, and legal/terms considerations documented in
    the Garage61 spike.
    """

    def find_reference_lap(
        self, simulator: str, car: str, track: str
    ) -> ReferenceLapCandidate:
        """Not implemented. See the Garage61 spike documentation."""
        raise NotImplementedError(_NOT_IMPLEMENTED_MESSAGE)

    def get_reference_csv_path(self, reference_lap: ReferenceLapCandidate) -> str:
        """Not implemented. See the Garage61 spike documentation."""
        raise NotImplementedError(_NOT_IMPLEMENTED_MESSAGE)
