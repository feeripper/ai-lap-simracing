"""Tests for coaching analysis module."""

from __future__ import annotations

import pandas as pd
import pytest

from src.analysis.coaching import (
    estimate_time_loss_from_speed,
    generate_coaching_analysis,
    generate_diagnosis,
    identify_strongest_loss_areas,
    infer_driving_issue,
    recommend_training_action,
)


def test_estimate_time_loss_from_speed_with_loss():
    """Test time loss estimation when user is slower than reference."""
    comparison = {
        "overall": {"metrics": {"speed": {"mean_diff": -10.0}}},
        "sectors": [
            {
                "name": "Sector 1",
                "metrics": {"speed": {"mean_diff": -8.0, "mean_abs_diff": 8.0}}
            },
            {
                "name": "Sector 2",
                "metrics": {"speed": {"mean_diff": -12.0, "mean_abs_diff": 12.0}}
            },
        ]
    }

    result = estimate_time_loss_from_speed(comparison)

    assert "total_time_loss_seconds" in result
    assert result["total_time_loss_seconds"] > 0
    assert len(result["sectors"]) == 2
    assert result["sectors"][0]["name"] == "Sector 1"
    assert result["sectors"][0]["time_loss_seconds"] > 0
    assert result["sectors"][0]["severity"] in ["low", "medium", "high"]


def test_estimate_time_loss_from_speed_no_loss():
    """Test time loss estimation when user matches reference speed."""
    comparison = {
        "overall": {"metrics": {"speed": {"mean_diff": 0.0}}},
        "sectors": [
            {
                "name": "Sector 1",
                "metrics": {"speed": {"mean_diff": 0.0, "mean_abs_diff": 0.0}}
            }
        ]
    }

    result = estimate_time_loss_from_speed(comparison)

    assert result["total_time_loss_seconds"] == 0.0
    assert result["sectors"][0]["time_loss_seconds"] == 0.0
    assert result["sectors"][0]["severity"] == "low"


def test_estimate_time_loss_from_speed_empty_sectors():
    """Test time loss estimation with no sectors."""
    comparison = {"overall": {"metrics": {}}, "sectors": []}

    result = estimate_time_loss_from_speed(comparison)

    assert result["total_time_loss_seconds"] == 0.0
    assert result["sectors"] == []


def test_identify_strongest_loss_areas():
    """Test identification of sectors with highest time loss."""
    time_loss = {
        "total_time_loss_seconds": 1.5,
        "sectors": [
            {"name": "Sector 1", "time_loss_seconds": 0.3, "severity": "medium"},
            {"name": "Sector 2", "time_loss_seconds": 0.8, "severity": "high"},
            {"name": "Sector 3", "time_loss_seconds": 0.4, "severity": "medium"},
        ]
    }

    result = identify_strongest_loss_areas(time_loss)

    assert len(result) == 3
    assert result[0]["name"] == "Sector 2"  # Highest loss
    assert result[0]["time_loss_seconds"] == 0.8
    assert result[-1]["name"] == "Sector 1"  # Lowest loss


def test_identify_strongest_loss_areas_no_loss():
    """Test identification when no time loss."""
    time_loss = {
        "total_time_loss_seconds": 0.0,
        "sectors": [
            {"name": "Sector 1", "time_loss_seconds": 0.0, "severity": "low"}
        ]
    }

    result = identify_strongest_loss_areas(time_loss)

    assert len(result) == 0


def test_infer_driving_issue_speed_loss():
    """Test driving issue inference for speed loss."""
    comparison = {
        "overall": {
            "metrics": {
                "speed": {"mean_diff": -15.0},
                "throttle": {"mean_diff": 0.0},
                "brake": {"mean_diff": 0.0}
            }
        }
    }
    time_loss = {"total_time_loss_seconds": 1.0, "sectors": []}

    result = infer_driving_issue(comparison, time_loss)

    assert "velocidade" in result.lower()


def test_infer_driving_issue_throttle_loss():
    """Test driving issue inference for throttle loss."""
    comparison = {
        "overall": {
            "metrics": {
                "speed": {"mean_diff": -2.0},
                "throttle": {"mean_diff": -0.2},
                "brake": {"mean_diff": 0.0}
            }
        }
    }
    time_loss = {"total_time_loss_seconds": 0.5, "sectors": []}

    result = infer_driving_issue(comparison, time_loss)

    assert "acelerador" in result.lower()


def test_infer_driving_issue_brake_excess():
    """Test driving issue inference for excessive braking."""
    comparison = {
        "overall": {
            "metrics": {
                "speed": {"mean_diff": 0.0},
                "throttle": {"mean_diff": 0.0},
                "brake": {"mean_diff": 0.3}
            }
        }
    }
    time_loss = {"total_time_loss_seconds": 0.3, "sectors": []}

    result = infer_driving_issue(comparison, time_loss)

    assert "freio" in result.lower()


def test_infer_driving_issue_no_issue():
    """Test driving issue inference when no significant issues."""
    comparison = {
        "overall": {
            "metrics": {
                "speed": {"mean_diff": 0.0},
                "throttle": {"mean_diff": 0.0},
                "brake": {"mean_diff": 0.0}
            }
        }
    }
    time_loss = {"total_time_loss_seconds": 0.0, "sectors": []}

    result = infer_driving_issue(comparison, time_loss)

    assert "bom trabalho" in result.lower()


def test_recommend_training_action_speed():
    """Test training recommendation for speed loss."""
    comparison = {
        "overall": {
            "metrics": {
                "speed": {"mean_diff": -10.0},
                "throttle": {"mean_diff": 0.0},
                "brake": {"mean_diff": 0.0}
            }
        }
    }
    time_loss = {
        "total_time_loss_seconds": 0.5,
        "sectors": [{"name": "Sector 1", "time_loss_seconds": 0.5, "severity": "high"}]
    }
    driving_issue = "velocidade abaixo da referência"

    result = recommend_training_action(comparison, time_loss, driving_issue)

    assert "treine" in result.lower()
    assert "sector 1" in result.lower()


def test_recommend_training_action_brake():
    """Test training recommendation for excessive braking."""
    comparison = {
        "overall": {
            "metrics": {
                "speed": {"mean_diff": 0.0},
                "throttle": {"mean_diff": 0.0},
                "brake": {"mean_diff": 0.2}
            }
        }
    }
    time_loss = {
        "total_time_loss_seconds": 0.3,
        "sectors": [{"name": "Sector 2", "time_loss_seconds": 0.3, "severity": "medium"}]
    }
    driving_issue = "uso excessivo de freio"

    result = recommend_training_action(comparison, time_loss, driving_issue)

    assert "treine" in result.lower()
    assert "frenagem" in result.lower() or "freio" in result.lower()


def test_recommend_training_action_no_loss():
    """Test training recommendation when no time loss."""
    comparison = {
        "overall": {
            "metrics": {
                "speed": {"mean_diff": 0.0},
                "throttle": {"mean_diff": 0.0},
                "brake": {"mean_diff": 0.0}
            }
        }
    }
    time_loss = {
        "total_time_loss_seconds": 0.0,
        "sectors": []
    }
    driving_issue = "Sua volta está muito próxima da referência. Bom trabalho!"

    result = recommend_training_action(comparison, time_loss, driving_issue)

    assert "continue" in result.lower() or "praticando" in result.lower()


def test_generate_coaching_analysis_complete():
    """Test complete coaching analysis generation."""
    comparison = {
        "overall": {
            "metrics": {
                "speed": {"mean_diff": -10.0},
                "throttle": {"mean_diff": -0.15},
                "brake": {"mean_diff": 0.0}
            }
        },
        "sectors": [
            {
                "name": "Sector 1",
                "metrics": {"speed": {"mean_diff": -8.0, "mean_abs_diff": 8.0}}
            }
        ]
    }

    result = generate_coaching_analysis(comparison)

    assert "time_loss" in result
    assert "strongest_loss_areas" in result
    assert "driving_issue" in result
    assert "training_recommendation" in result

    assert result["time_loss"]["total_time_loss_seconds"] > 0
    assert len(result["strongest_loss_areas"]) > 0
    assert isinstance(result["driving_issue"], str)
    assert isinstance(result["training_recommendation"], str)


def test_coaching_with_garage61_csv_format(tmp_path):
    """Test coaching analysis with Garage61 CSV format (LapDistPct, Speed)."""
    # Create user CSV in Garage61 format
    user_csv = tmp_path / "user_garage61.csv"
    user_data = pd.DataFrame({
        "LapDistPct": [0, 25, 50, 75, 100],
        "Speed": [180, 170, 160, 175, 185],
        "Throttle": [0.9, 0.8, 0.7, 0.9, 0.8],
        "Brake": [0, 0.1, 0.2, 0, 0],
    })
    user_data.to_csv(user_csv, index=False)

    # Create reference CSV in Garage61 format
    reference_csv = tmp_path / "reference_garage61.csv"
    reference_data = pd.DataFrame({
        "LapDistPct": [0, 25, 50, 75, 100],
        "Speed": [200, 190, 180, 195, 205],
        "Throttle": [1.0, 0.9, 0.8, 1.0, 0.9],
        "Brake": [0, 0, 0.1, 0, 0],
    })
    reference_data.to_csv(reference_csv, index=False)

    # Run analysis through pipeline
    from src.analysis.pipeline import analyze_lap_files
    result = analyze_lap_files(str(user_csv), str(reference_csv))

    # Verify coaching output is present
    assert "coaching" in result
    assert "time_loss" in result["coaching"]
    assert "driving_issue" in result["coaching"]
    assert "training_recommendation" in result["coaching"]

    # Verify time loss is detected
    assert result["coaching"]["time_loss"]["total_time_loss_seconds"] > 0


def test_coaching_with_internal_csv_format(tmp_path):
    """Test coaching analysis with internal CSV format (lap_dist_pct, speed)."""
    # Create user CSV in internal format
    user_csv = tmp_path / "user_internal.csv"
    user_data = pd.DataFrame({
        "lap_dist_pct": [0, 25, 50, 75, 100],
        "speed": [180, 170, 160, 175, 185],
        "throttle": [0.9, 0.8, 0.7, 0.9, 0.8],
        "brake": [0, 0.1, 0.2, 0, 0],
    })
    user_data.to_csv(user_csv, index=False)

    # Create reference CSV in internal format
    reference_csv = tmp_path / "reference_internal.csv"
    reference_data = pd.DataFrame({
        "lap_dist_pct": [0, 25, 50, 75, 100],
        "speed": [200, 190, 180, 195, 205],
        "throttle": [1.0, 0.9, 0.8, 1.0, 0.9],
        "brake": [0, 0, 0.1, 0, 0],
    })
    reference_data.to_csv(reference_csv, index=False)

    # Run analysis through pipeline
    from src.analysis.pipeline import analyze_lap_files
    result = analyze_lap_files(str(user_csv), str(reference_csv))

    # Verify coaching output is present
    assert "coaching" in result
    assert "time_loss" in result["coaching"]
    assert "driving_issue" in result["coaching"]
    assert "training_recommendation" in result["coaching"]


def test_coaching_with_missing_speed_column(tmp_path):
    """Test coaching analysis when speed column is missing."""
    # Create CSVs without speed column
    user_csv = tmp_path / "user_no_speed.csv"
    user_data = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "throttle": [0.9, 1.0, 0.8],
        "brake": [0, 0, 0.5],
    })
    user_data.to_csv(user_csv, index=False)

    reference_csv = tmp_path / "reference_no_speed.csv"
    reference_data = pd.DataFrame({
        "lap_dist_pct": [0, 50, 100],
        "throttle": [1.0, 1.0, 1.0],
        "brake": [0, 0, 0],
    })
    reference_data.to_csv(reference_csv, index=False)

    # Run analysis through pipeline
    from src.analysis.pipeline import analyze_lap_files
    result = analyze_lap_files(str(user_csv), str(reference_csv))

    # Coaching should still work, but time loss will be 0
    assert "coaching" in result
    assert result["coaching"]["time_loss"]["total_time_loss_seconds"] == 0.0


def test_generate_diagnosis_with_time_loss():
    """Test diagnosis generation with time loss."""
    comparison = {
        "overall": {
            "metrics": {
                "speed": {"mean_diff": -10.0},
                "throttle": {"mean_diff": -0.15},
                "brake": {"mean_diff": 0.0}
            }
        },
        "sectors": [
            {
                "name": "Sector 1",
                "metrics": {"speed": {"mean_diff": -8.0, "mean_abs_diff": 8.0}}
            },
            {
                "name": "Sector 2",
                "metrics": {"speed": {"mean_diff": -12.0, "mean_abs_diff": 12.0}}
            }
        ]
    }

    result = generate_diagnosis(comparison)

    assert "overall_lap_delta_seconds" in result
    assert "summary" in result
    assert "priority_items" in result
    assert "likely_driver_issue" in result
    assert "training_focus" in result

    assert result["overall_lap_delta_seconds"] > 0
    assert "perdendo" in result["summary"].lower()
    assert len(result["priority_items"]) > 0
    assert result["priority_items"][0]["priority"] == 1
    assert "location" in result["priority_items"][0]
    assert "why" in result["priority_items"][0]
    assert "what_to_train" in result["priority_items"][0]


def test_generate_diagnosis_priority_ordering():
    """Test that priority items are ordered by time loss (highest first)."""
    comparison = {
        "overall": {"metrics": {"speed": {"mean_diff": -10.0}}},
        "sectors": [
            {
                "name": "Sector 1",
                "metrics": {"speed": {"mean_diff": -5.0, "mean_abs_diff": 5.0}}
            },
            {
                "name": "Sector 2",
                "metrics": {"speed": {"mean_diff": -15.0, "mean_abs_diff": 15.0}}
            },
            {
                "name": "Sector 3",
                "metrics": {"speed": {"mean_diff": -8.0, "mean_abs_diff": 8.0}}
            }
        ]
    }

    result = generate_diagnosis(comparison)

    # Should have 3 priority items
    assert len(result["priority_items"]) == 3

    # Priority 1 should be Sector 2 (highest loss)
    assert result["priority_items"][0]["priority"] == 1
    assert result["priority_items"][0]["location"] == "Sector 2"

    # Priority 2 should be Sector 3 (second highest)
    assert result["priority_items"][1]["priority"] == 2
    assert result["priority_items"][1]["location"] == "Sector 3"

    # Priority 3 should be Sector 1 (lowest loss)
    assert result["priority_items"][2]["priority"] == 3
    assert result["priority_items"][2]["location"] == "Sector 1"


def test_generate_diagnosis_no_time_loss():
    """Test diagnosis when no time loss (good lap)."""
    comparison = {
        "overall": {
            "metrics": {
                "speed": {"mean_diff": 0.0},
                "throttle": {"mean_diff": 0.0},
                "brake": {"mean_diff": 0.0}
            }
        },
        "sectors": [
            {
                "name": "Sector 1",
                "metrics": {"speed": {"mean_diff": 0.0, "mean_abs_diff": 0.0}}
            }
        ]
    }

    result = generate_diagnosis(comparison)

    assert result["overall_lap_delta_seconds"] == 0.0
    assert "bom trabalho" in result["summary"].lower()
    assert len(result["priority_items"]) == 0


def test_generate_diagnosis_fallback_no_sector_names():
    """Test diagnosis fallback when sector names are unavailable."""
    comparison = {
        "overall": {
            "metrics": {
                "speed": {"mean_diff": -10.0},
                "throttle": {"mean_diff": -0.1},
                "brake": {"mean_diff": 0.0}
            }
        },
        "sectors": []  # No sectors
    }

    result = generate_diagnosis(comparison)

    # Should still generate a diagnosis with fallback
    assert result["overall_lap_delta_seconds"] > 0
    assert len(result["priority_items"]) == 1
    assert result["priority_items"][0]["location"] == "Setor desconhecido"
    assert result["priority_items"][0]["priority"] == 1


def test_generate_diagnosis_clear_recommendation_text():
    """Test that recommendation text is clear and actionable."""
    comparison = {
        "overall": {
            "metrics": {
                "speed": {"mean_diff": -12.0},
                "throttle": {"mean_diff": -0.2},
                "brake": {"mean_diff": 0.0}
            }
        },
        "sectors": [
            {
                "name": "Sector 1",
                "metrics": {
                    "speed": {"mean_diff": -12.0, "mean_abs_diff": 12.0},
                    "throttle": {"mean_diff": -0.2, "mean_abs_diff": 0.2}
                }
            }
        ]
    }

    result = generate_diagnosis(comparison)

    # Check that "why" is clear
    why = result["priority_items"][0]["why"]
    assert "mais lento" in why.lower() or "acelerador" in why.lower()

    # Check that "what_to_train" is actionable
    what_to_train = result["priority_items"][0]["what_to_train"]
    assert "pratique" in what_to_train.lower()


def test_generate_diagnosis_empty_comparison():
    """Test diagnosis with empty/invalid comparison."""
    comparison = {"overall": {"metrics": {}}, "sectors": []}

    result = generate_diagnosis(comparison)

    # Should handle gracefully
    assert result["overall_lap_delta_seconds"] == 0.0
    assert "summary" in result
    assert "priority_items" in result
    assert isinstance(result["priority_items"], list)


def test_generate_diagnosis_with_garage61_csv_format(tmp_path):
    """Test diagnosis with Garage61 CSV format through pipeline."""
    user_csv = tmp_path / "user_garage61.csv"
    user_data = pd.DataFrame({
        "LapDistPct": [0, 25, 50, 75, 100],
        "Speed": [180, 170, 160, 175, 185],
        "Throttle": [0.9, 0.8, 0.7, 0.9, 0.8],
        "Brake": [0, 0.1, 0.2, 0, 0],
    })
    user_data.to_csv(user_csv, index=False)

    reference_csv = tmp_path / "reference_garage61.csv"
    reference_data = pd.DataFrame({
        "LapDistPct": [0, 25, 50, 75, 100],
        "Speed": [200, 190, 180, 195, 205],
        "Throttle": [1.0, 0.9, 0.8, 1.0, 0.9],
        "Brake": [0, 0, 0.1, 0, 0],
    })
    reference_data.to_csv(reference_csv, index=False)

    from src.analysis.pipeline import analyze_lap_files
    result = analyze_lap_files(str(user_csv), str(reference_csv))

    # Generate diagnosis from comparison
    diagnosis = generate_diagnosis(result["comparison"])

    assert "overall_lap_delta_seconds" in diagnosis
    assert "priority_items" in diagnosis
    assert len(diagnosis["priority_items"]) > 0
