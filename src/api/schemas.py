"""Pydantic schemas for the API responses."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SimulatorOut(BaseModel):
    """Simulator representation for API responses."""

    id: int
    name: str

    model_config = {"from_attributes": True}


class CarOut(BaseModel):
    """Car representation for API responses."""

    id: int
    name: str

    model_config = {"from_attributes": True}


class TrackOut(BaseModel):
    """Track representation for API responses."""

    id: int
    name: str

    model_config = {"from_attributes": True}


class ReferenceLapOut(BaseModel):
    """Reference lap representation for API responses."""

    id: int
    driver_name: str
    lap_time_seconds: float
    csv_path: str
    is_active: bool
    simulator: str
    car: str
    track: str
    source: str = "manual"
    source_lap_id: Optional[str] = None
    source_url: Optional[str] = None
    track_layout: Optional[str] = None
    imported_at: Optional[datetime] = None
    file_checksum: Optional[str] = None
    validation_status: str = "validated"
    raw_metadata_json: Optional[str] = None
    notes: Optional[str] = None


class CatalogOut(BaseModel):
    """Catalog of simulators, cars, and tracks for API responses."""

    simulators: list[SimulatorOut]
    cars: list[CarOut]
    tracks: list[TrackOut]


class AnalysisRunSummaryOut(BaseModel):
    """Summary representation of a persisted analysis run."""

    id: int
    created_at: datetime
    simulator_name: Optional[str] = None
    car_name: Optional[str] = None
    track_name: Optional[str] = None
    analysis_type: str
    summary: Optional[str] = None
    priority: Optional[str] = None

    model_config = {"from_attributes": True}
