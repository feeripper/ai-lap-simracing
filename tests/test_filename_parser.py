"""Tests for Garage61 filename parsing."""

import pytest

from src.filename_parser import lap_time_to_seconds, parse_filename


@pytest.mark.parametrize(
    ("filename", "driver", "car", "track", "lap_time", "lap_time_seconds"),
    [
        (
            "Garage61_FelippeAraujo_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.56.068.csv",
            "FelippeAraujo",
            "AudiRS3LMSGen2TCR",
            "WatkinsGlenInternational(Boot)",
            "01.56.068",
            116.068,
        ),
        (
            "Garage61_DanielLewis_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.53.244.csv",
            "DanielLewis",
            "AudiRS3LMSGen2TCR",
            "WatkinsGlenInternational(Boot)",
            "01.53.244",
            113.244,
        ),
        (
            "Garage61_RomanRichtr_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.53.472.csv",
            "RomanRichtr",
            "AudiRS3LMSGen2TCR",
            "WatkinsGlenInternational(Boot)",
            "01.53.472",
            113.472,
        ),
        (
            "Garage61_TravisBumgarner_AudiRS3LMSGen2TCR_WatkinsGlenInternational(Boot)_01.55.695.csv",
            "TravisBumgarner",
            "AudiRS3LMSGen2TCR",
            "WatkinsGlenInternational(Boot)",
            "01.55.695",
            115.695,
        ),
    ],
)
def test_parse_garage61_filename(
    filename: str,
    driver: str,
    car: str,
    track: str,
    lap_time: str,
    lap_time_seconds: float,
) -> None:
    metadata = parse_filename(filename)
    assert metadata.original_filename == filename
    assert metadata.driver == driver
    assert metadata.car == car
    assert metadata.track == track
    assert metadata.lap_time == lap_time
    assert metadata.lap_time_seconds == pytest.approx(lap_time_seconds)


def test_parse_unknown_filename_extracts_lap_time_only() -> None:
    metadata = parse_filename("custom_lap_export_01.53.244.csv")
    assert metadata.driver is None
    assert metadata.car is None
    assert metadata.track is None
    assert metadata.lap_time == "01.53.244"
    assert metadata.lap_time_seconds == pytest.approx(113.244)


def test_parse_filename_without_lap_time() -> None:
    metadata = parse_filename("unknown_format.csv")
    assert metadata.lap_time is None
    assert metadata.lap_time_seconds is None


def test_lap_time_to_seconds() -> None:
    assert lap_time_to_seconds("01.53.244") == pytest.approx(113.244)
    assert lap_time_to_seconds("01.56.068") == pytest.approx(116.068)
