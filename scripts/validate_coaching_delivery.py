"""Manual validation script for the coaching delivery backend.

Runs a representative end-to-end analysis using TestClient and prints the
canonical response and summary list.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from src.api.dependencies import get_db
from src.api.main import app
from src.db import SessionLocal, init_db
from src.db.models import Base
from src.db.repository import create_analysis_run, create_car, create_reference_lap, create_simulator, create_track


def _make_csv(path: Path, speed_offset: float = 0.0) -> None:
    pd.DataFrame({
        "lap_dist_pct": [0, 25, 50, 75, 100],
        "speed": [200.0 + speed_offset, 190.0 + speed_offset, 180.0 + speed_offset, 195.0 + speed_offset, 205.0 + speed_offset],
        "throttle": [1.0, 1.0, 0.8, 0.9, 1.0],
        "brake": [0.0, 0.0, 0.2, 0.0, 0.0],
    }).to_csv(path, index=False)


def _reset_db():
    engine = SessionLocal().bind
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def main():
    _reset_db()
    init_db()

    db = SessionLocal()
    simulator = create_simulator(db, name="iRacing")
    car = create_car(db, name="Toyota GR86")
    track = create_track(db, name="Spa-Francorchamps")

    with tempfile.TemporaryDirectory() as temp_dir:
        user_csv = Path(temp_dir) / "user.csv"
        reference_csv = Path(temp_dir) / "reference.csv"
        _make_csv(reference_csv, speed_offset=0.0)
        _make_csv(user_csv, speed_offset=-15.0)

        create_reference_lap(
            db,
            simulator_id=simulator.id,
            car_id=car.id,
            track_id=track.id,
            driver_name="Reference",
            lap_time_seconds=120.0,
            csv_path=str(reference_csv),
            is_active=True,
        )

        def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        with user_csv.open("rb") as uf:
            response = client.post(
                "/analyze-with-reference",
                files={"user_csv": ("user.csv", uf, "text/csv")},
                data={
                    "simulator": "iRacing",
                    "car": "Toyota GR86",
                    "track": "Spa-Francorchamps",
                },
            )

    print("=" * 80)
    print("Manual validation: /analyze-with-reference")
    print("=" * 80)
    print(f"status_code: {response.status_code}")
    body = response.json()
    print(f"analysis_id: {body['analysis_id']}")
    print(f"status: {body['status']}")
    print(f"diagnosis_version: {body['diagnosis_version']}")
    print(f"processing_time_ms: {body['processing_time_ms']}")
    print(f"number_of_opportunities: {len(body['top_opportunities'])}")
    if body['top_opportunities']:
        first = body['top_opportunities'][0]
        print(f"first_opportunity: {json.dumps(first, ensure_ascii=False, indent=2)}")
    print(f"training_plan: {json.dumps(body['training_plan'], ensure_ascii=False, indent=2)}")
    print(f"warnings: {body['warnings']}")

    analysis_id = body['analysis_id']
    get_response = client.get(f"/analyses/{analysis_id}")
    print("\n" + "=" * 80)
    print(f"GET /analyses/{analysis_id}")
    print("=" * 80)
    print(f"status_code: {get_response.status_code}")
    get_body = get_response.json()
    print(f"analysis_id_match: {get_body['analysis_id'] == analysis_id}")
    print(f"diagnosis_version: {get_body['diagnosis_version']}")
    print(f"top_opportunities_count: {len(get_body['top_opportunities'])}")

    list_response = client.get("/analyses")
    print("\n" + "=" * 80)
    print("GET /analyses")
    print("=" * 80)
    print(f"status_code: {list_response.status_code}")
    summaries = list_response.json()
    print(f"number_of_summaries: {len(summaries)}")
    if summaries:
        summary = summaries[0]
        print(f"summary: {json.dumps(summary, ensure_ascii=False, indent=2, default=str)}")

    db.close()
    app.dependency_overrides.clear()


if __name__ == "__main__":
    main()
