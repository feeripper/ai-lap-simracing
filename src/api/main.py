"""FastAPI application for AI Lap Simracing."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.analysis.pipeline import analyze_lap_files
from src.api.dependencies import get_db
from src.db.repository import (
    get_active_reference_lap,
    get_car_by_name,
    get_simulator_by_name,
    get_track_by_name,
)

app = FastAPI(title="AI Lap Simracing API")

# TEMPORARY MVP catalog. This will be replaced by database-backed catalog
# in a future PR (see PR13). Do not rely on these fixed values long term.
_MVP_CATALOG = {
    "simulators": ["iRacing"],
    "cars": ["Toyota GR86"],
    "tracks": ["Spa"],
}


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


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-lap-simracing"}


@app.get("/catalog")
def catalog():
    """Return the MVP catalog of available simulators, cars, and tracks.

    NOTE: This currently returns a fixed MVP catalog. It will be replaced by a
    database-backed catalog in a future PR.
    """
    return _MVP_CATALOG


@app.post("/analyze")
def analyze(
    user_csv: UploadFile = File(...),
    reference_csv: UploadFile = File(...),
    distance_column: str = Form("lap_dist_pct"),
    num_points: int = Form(101),
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

    return result


@app.post("/analyze-with-reference")
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

    simulator_obj = get_simulator_by_name(db, simulator)
    if not simulator_obj:
        raise HTTPException(status_code=404, detail=f"simulator not found: {simulator}")

    car_obj = get_car_by_name(db, car)
    if not car_obj:
        raise HTTPException(status_code=404, detail=f"car not found: {car}")

    track_obj = get_track_by_name(db, track)
    if not track_obj:
        raise HTTPException(status_code=404, detail=f"track not found: {track}")

    reference_lap = get_active_reference_lap(
        db,
        simulator_id=simulator_obj.id,
        car_id=car_obj.id,
        track_id=track_obj.id,
    )
    if not reference_lap:
        raise HTTPException(
            status_code=404,
            detail=(
                f"active reference lap not found for simulator '{simulator}', "
                f"car '{car}', track '{track}'"
            ),
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        user_csv_path = _save_upload_to_temp(user_csv, temp_dir)

        try:
            result = analyze_lap_files(
                user_csv_path=user_csv_path,
                reference_csv_path=reference_lap.csv_path,
                distance_column=distance_column,
                num_points=num_points,
            )
        except (ValueError, FileNotFoundError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")

    return result
