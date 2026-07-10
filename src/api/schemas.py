"""Pydantic schemas for the API responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


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


class CoachingOpportunityOut(BaseModel):
    """A single coaching opportunity for time improvement."""

    rank: int = Field(..., ge=1, le=3)
    corner: str
    corner_name: Optional[str] = None
    phase: str
    estimated_time_loss: float = Field(..., ge=0)
    confidence: str
    evidence: dict[str, Any]
    probable_cause: str
    recommendation: str
    training_focus: Optional[str] = None


class TrainingPlanOut(BaseModel):
    """Training plan derived from top opportunities."""

    primary_focus: Optional[str] = None
    suggested_laps: int = 0
    target_corners: list[str] = []
    instructions: list[str] = []
    measurable_target: Optional[str] = None
    secondary_focuses: list[str] = []


class AnalysisDetailOut(BaseModel):
    """Full canonical response for an analysis run."""

    analysis_id: int
    analysis_run_id: int
    status: str = "completed"
    diagnosis_version: str = "1.0"
    processing_time_ms: float = Field(..., ge=0)
    simulator: Optional[str] = None
    car: Optional[str] = None
    track: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None
    comparison: Optional[dict[str, Any]] = None
    insights: Optional[dict[str, Any]] = None
    diagnosis: Optional[dict[str, Any]] = None
    top_opportunities: list[CoachingOpportunityOut] = []
    training_plan: TrainingPlanOut = TrainingPlanOut()
    warnings: list[str] = []


class AnalysisSummaryResponseOut(BaseModel):
    """Lightweight summary for analysis list endpoint."""

    id: int
    analysis_id: int
    created_at: datetime
    status: str = "completed"
    diagnosis_version: str = "1.0"
    simulator: Optional[str] = None
    car: Optional[str] = None
    track: Optional[str] = None
    analysis_type: str
    total_time_loss: Optional[float] = None
    number_of_opportunities: int = 0
    primary_focus: Optional[str] = None
    summary: Optional[str] = None
    priority: Optional[str] = None
