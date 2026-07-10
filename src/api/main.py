"""FastAPI application for AI Lap Simracing."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from src.analysis.pipeline import analyze_lap_files
from src.api.dependencies import get_db
from src.api.schemas import (
    AnalysisDetailOut,
    AnalysisRunSummaryOut,
    AnalysisSummaryResponseOut,
    CarOut,
    CatalogOut,
    ReferenceLapOut,
    SimulatorOut,
    TrackOut,
)
from src.api.serialization import safe_json_dumps, safe_jsonable
from src.db.repository import (
    create_analysis_run,
    get_all_cars,
    get_all_simulators,
    get_all_tracks,
    get_analysis_run_by_id,
    list_all_reference_laps,
    list_analysis_runs,
)
from src.reference_providers.exceptions import (
    ActiveReferenceLapNotFoundError,
    CarNotFoundError,
    SimulatorNotFoundError,
    TrackNotFoundError,
)
from src.reference_providers.local import LocalReferenceLapProvider

app = FastAPI(title="AI Lap Simracing API")

# CORS for the local Vite frontend (development).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _validate_csv_upload(upload: UploadFile, field_name: str) -> None:
    """Validate that an uploaded file has a .csv extension."""
    filename = upload.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be a .csv file",
        )


def _save_upload_to_temp(upload: UploadFile, temp_dir: str) -> str:
    """Save an uploaded file to a temporary directory and return its path."""
    filename = Path(upload.filename or "upload.csv").name
    dest_path = Path(temp_dir) / filename
    with dest_path.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)
    return str(dest_path)


def _persist_analysis_run(
    db: Session,
    result: dict,
    analysis_type: str,
    user_csv_filename: str | None,
    reference_csv_path: str | None,
    simulator_name: str | None = None,
    car_name: str | None = None,
    track_name: str | None = None,
) -> int:
    """Persist an analysis result and return the created analysis run id."""
    insights = result.get("insights", {}) or {}
    analysis_run = create_analysis_run(
        db,
        analysis_type=analysis_type,
        result_json=safe_json_dumps(result, ensure_ascii=False),
        simulator_name=simulator_name,
        car_name=car_name,
        track_name=track_name,
        user_csv_filename=user_csv_filename,
        reference_csv_path=reference_csv_path,
        summary=insights.get("summary"),
        priority=insights.get("priority"),
    )
    return analysis_run.id


def _build_analysis_response_from_dict(result: dict, analysis_id: int) -> dict:
    """Build a canonical analysis response from a fresh pipeline result."""
    status = result.get("status", "completed")
    diagnosis_version = result.get("diagnosis_version", "1.0")
    processing_time_ms = result.get("processing_time_ms", 0.0)
    warnings = result.get("warnings", [])
    metadata = result.get("metadata", {})
    comparison = result.get("comparison")
    insights = result.get("insights")
    diagnosis = result.get("diagnosis")
    top_opportunities = result.get("top_opportunities", [])
    training_plan = result.get("training_plan", {})

    # If this is an older record without top-level top_opportunities, derive from diagnosis
    if not top_opportunities and diagnosis:
        top_opportunities = diagnosis.get("top_opportunities", [])
        training_plan = diagnosis.get("training_plan", {})

    response = {
        "analysis_id": analysis_id,
        "analysis_run_id": analysis_id,
        "status": status,
        "diagnosis_version": diagnosis_version,
        "processing_time_ms": processing_time_ms,
        "simulator": result.get("simulator"),
        "car": result.get("car"),
        "track": result.get("track"),
        "created_at": None,
        "metadata": safe_jsonable(metadata),
        "comparison": safe_jsonable(comparison),
        "insights": safe_jsonable(insights),
        "diagnosis": safe_jsonable(diagnosis),
        "top_opportunities": safe_jsonable(top_opportunities),
        "training_plan": safe_jsonable(training_plan),
        "warnings": safe_jsonable(warnings),
    }

    return response


def _build_analysis_response(run: Any) -> dict:
    """Build a canonical analysis response from a persisted AnalysisRun.

    Ensures older records without new fields still produce a valid response.
    """
    result = json.loads(run.result_json)
    response = _build_analysis_response_from_dict(result, run.id)
    response["created_at"] = run.created_at
    response["simulator"] = run.simulator_name
    response["car"] = run.car_name
    response["track"] = run.track_name
    return response


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-lap-simracing"}


@app.get("/catalog", response_model=CatalogOut)
def catalog(db: Session = Depends(get_db)):
    """Return the catalog of simulators, cars, and tracks from the database.

    If the database is empty, empty lists are returned without error.
    """
    return CatalogOut(
        simulators=[SimulatorOut.model_validate(s) for s in get_all_simulators(db)],
        cars=[CarOut.model_validate(c) for c in get_all_cars(db)],
        tracks=[TrackOut.model_validate(t) for t in get_all_tracks(db)],
    )


@app.get("/simulators", response_model=list[SimulatorOut])
def list_simulators(db: Session = Depends(get_db)):
    """List all simulators from the database."""
    return [SimulatorOut.model_validate(s) for s in get_all_simulators(db)]


@app.get("/cars", response_model=list[CarOut])
def list_cars(db: Session = Depends(get_db)):
    """List all cars from the database."""
    return [CarOut.model_validate(c) for c in get_all_cars(db)]


@app.get("/tracks", response_model=list[TrackOut])
def list_tracks(db: Session = Depends(get_db)):
    """List all tracks from the database."""
    return [TrackOut.model_validate(t) for t in get_all_tracks(db)]


@app.get("/reference-laps", response_model=list[ReferenceLapOut])
def list_reference_laps(db: Session = Depends(get_db)):
    """List all reference laps from the database with related entity names."""
    laps = list_all_reference_laps(db)
    return [
        ReferenceLapOut(
            id=lap.id,
            driver_name=lap.driver_name,
            lap_time_seconds=lap.lap_time_seconds,
            csv_path=lap.csv_path,
            is_active=lap.is_active,
            simulator=lap.simulator.name,
            car=lap.car.name,
            track=lap.track.name,
            source=lap.source,
            source_lap_id=lap.source_lap_id,
            source_url=lap.source_url,
            track_layout=lap.track_layout,
            imported_at=lap.imported_at,
            file_checksum=lap.file_checksum,
            validation_status=lap.validation_status,
            raw_metadata_json=lap.raw_metadata_json,
            notes=lap.notes,
        )
        for lap in laps
    ]


@app.post("/analyze", response_model=AnalysisDetailOut)
def analyze(
    user_csv: UploadFile = File(...),
    reference_csv: UploadFile = File(...),
    distance_column: str = Form("lap_dist_pct"),
    num_points: int = Form(101),
    db: Session = Depends(get_db),
):
    """Analyze a user lap against a reference lap from two uploaded CSV files."""
    _validate_csv_upload(user_csv, "user_csv")
    _validate_csv_upload(reference_csv, "reference_csv")

    with tempfile.TemporaryDirectory() as temp_dir:
        user_csv_path = _save_upload_to_temp(user_csv, temp_dir)
        reference_csv_path = _save_upload_to_temp(reference_csv, temp_dir)

        try:
            result = analyze_lap_files(
                user_csv_path=user_csv_path,
                reference_csv_path=reference_csv_path,
                distance_column=distance_column,
                num_points=num_points,
            )
        except (ValueError, FileNotFoundError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")

    analysis_run_id = _persist_analysis_run(
        db,
        result=result,
        analysis_type="direct_upload",
        user_csv_filename=user_csv.filename,
        reference_csv_path=reference_csv.filename,
    )
    result["analysis_run_id"] = analysis_run_id

    return _build_analysis_response_from_dict(result, analysis_run_id)


@app.post("/analyze-with-reference", response_model=AnalysisDetailOut)
def analyze_with_reference(
    user_csv: UploadFile = File(...),
    simulator: str = Form(...),
    car: str = Form(...),
    track: str = Form(...),
    distance_column: str = Form("lap_dist_pct"),
    num_points: int = Form(101),
    db: Session = Depends(get_db),
):
    """Analyze a user lap against the active reference lap from the database."""
    _validate_csv_upload(user_csv, "user_csv")

    provider = LocalReferenceLapProvider(db)
    try:
        reference = provider.find_reference_lap(simulator, car, track)
    except (
        SimulatorNotFoundError,
        CarNotFoundError,
        TrackNotFoundError,
        ActiveReferenceLapNotFoundError,
    ) as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    reference_csv_path = provider.get_reference_csv_path(reference)

    with tempfile.TemporaryDirectory() as temp_dir:
        user_csv_path = _save_upload_to_temp(user_csv, temp_dir)

        try:
            result = analyze_lap_files(
                user_csv_path=user_csv_path,
                reference_csv_path=reference_csv_path,
                distance_column=distance_column,
                num_points=num_points,
            )
        except (ValueError, FileNotFoundError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")

    analysis_run_id = _persist_analysis_run(
        db,
        result=result,
        analysis_type="active_reference",
        user_csv_filename=user_csv.filename,
        reference_csv_path=reference_csv_path,
        simulator_name=simulator,
        car_name=car,
        track_name=track,
    )
    result["analysis_run_id"] = analysis_run_id
    result["simulator"] = simulator
    result["car"] = car
    result["track"] = track

    return _build_analysis_response_from_dict(result, analysis_run_id)


@app.get("/analyses", response_model=list[AnalysisSummaryResponseOut])
def list_analyses(db: Session = Depends(get_db)):
    """List all persisted analysis runs (summary view), most recent first."""
    runs = list_analysis_runs(db)
    summaries = []
    for run in runs:
        result = json.loads(run.result_json)
        diagnosis = result.get("diagnosis", {})
        top_opportunities = result.get("top_opportunities", diagnosis.get("top_opportunities", []))
        training_plan = result.get("training_plan", diagnosis.get("training_plan", {}))
        summaries.append({
            "id": run.id,
            "analysis_id": run.id,
            "created_at": run.created_at,
            "status": result.get("status", "completed"),
            "diagnosis_version": result.get("diagnosis_version", "1.0"),
            "simulator": run.simulator_name,
            "car": run.car_name,
            "track": run.track_name,
            "analysis_type": run.analysis_type,
            "total_time_loss": diagnosis.get("overall_lap_delta_seconds"),
            "number_of_opportunities": len(top_opportunities),
            "primary_focus": training_plan.get("primary_focus"),
            "summary": run.summary,
            "priority": run.priority,
        })
    return summaries


@app.get("/analyses/{analysis_id}", response_model=AnalysisDetailOut)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Return the full persisted analysis result for a given id."""
    run = get_analysis_run_by_id(db, analysis_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"analysis not found: {analysis_id}")

    return _build_analysis_response(run)
