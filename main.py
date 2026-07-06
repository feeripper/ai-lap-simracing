"""AI Lap Simracing — local telemetry analysis entry point."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from src.telemetry import TelemetryDiscoveryError, write_telemetry_summary

DATA_DIR = Path("data")
OUTPUT_PATH = Path("outputs/telemetry_summary.json")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        summary = write_telemetry_summary(DATA_DIR, OUTPUT_PATH)
    except TelemetryDiscoveryError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    user = summary["user_lap"]
    refs = summary["reference_laps"]
    print(f"User lap: {user['filename']} ({user['lap_time'] or 'no lap time'})")
    print(f"Reference laps: {len(refs)}")
    for ref in refs:
        print(f"  - {ref['filename']} ({ref['lap_time'] or 'no lap time'})")
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
