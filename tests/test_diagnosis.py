"""Tests for AI simracing coach diagnosis layer."""

from __future__ import annotations

import pandas as pd
import pytest

from src.analysis.diagnosis import (
    build_recommendation,
    calculate_confidence,
    classify_corner_phase,
    estimate_time_loss_from_speed,
    generate_diagnosis,
    generate_top_opportunities,
    generate_training_plan,
    infer_probable_cause,
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
    assert result["priority_items"][0]["location"] == "Full lap"
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


def test_generate_diagnosis_brake_issue():
    """Test diagnosis with excessive braking issue."""
    comparison = {
        "overall": {
            "metrics": {
                "speed": {"mean_diff": 0.0},
                "throttle": {"mean_diff": 0.0},
                "brake": {"mean_diff": 0.3}
            }
        },
        "sectors": [
            {
                "name": "Sector 1",
                "metrics": {
                    "speed": {"mean_diff": 0.0, "mean_abs_diff": 0.0},
                    "brake": {"mean_diff": 0.3, "mean_abs_diff": 0.3}
                }
            }
        ]
    }

    result = generate_diagnosis(comparison)

    assert "freio" in result["likely_driver_issue"].lower()
    assert "frenagem" in result["training_focus"].lower()


def test_generate_diagnosis_throttle_issue():
    """Test diagnosis with throttle issue."""
    comparison = {
        "overall": {
            "metrics": {
                "speed": {"mean_diff": -2.0},
                "throttle": {"mean_diff": -0.2},
                "brake": {"mean_diff": 0.0}
            }
        },
        "sectors": [
            {
                "name": "Sector 1",
                "metrics": {
                    "speed": {"mean_diff": -2.0, "mean_abs_diff": 2.0},
                    "throttle": {"mean_diff": -0.2, "mean_abs_diff": 0.2}
                }
            }
        ]
    }

    result = generate_diagnosis(comparison)

    assert "acelerador" in result["likely_driver_issue"].lower()
    assert "aceleração" in result["training_focus"].lower()


# New tests for Top 3 opportunities, phase classification, cause inference, confidence, and training plan


def test_classify_corner_phase_braking():
    """Test corner phase classification for braking."""
    metrics = {
        "speed": {"mean_diff": -5.0},
        "throttle": {"mean_diff": 0.0},
        "brake": {"mean_diff": 0.2}
    }
    phase = classify_corner_phase(metrics)
    assert phase == "braking"


def test_classify_corner_phase_entry():
    """Test corner phase classification for entry."""
    metrics = {
        "speed": {"mean_diff": -8.0},
        "throttle": {"mean_diff": -0.2},
        "brake": {"mean_diff": 0.0}
    }
    phase = classify_corner_phase(metrics)
    assert phase == "entry"


def test_classify_corner_phase_apex():
    """Test corner phase classification for apex."""
    metrics = {
        "speed": {"mean_diff": -15.0},
        "throttle": {"mean_diff": 0.0},
        "brake": {"mean_diff": 0.0}
    }
    phase = classify_corner_phase(metrics)
    assert phase == "apex"


def test_classify_corner_phase_exit():
    """Test corner phase classification for exit."""
    metrics = {
        "speed": {"mean_diff": -3.0},
        "throttle": {"mean_diff": -0.2},
        "brake": {"mean_diff": 0.0}
    }
    phase = classify_corner_phase(metrics)
    assert phase == "exit"


def test_classify_corner_phase_unknown():
    """Test corner phase classification for unknown."""
    metrics = {
        "speed": {"mean_diff": 0.0},
        "throttle": {"mean_diff": 0.0},
        "brake": {"mean_diff": 0.0}
    }
    phase = classify_corner_phase(metrics)
    assert phase == "unknown"


def test_infer_probable_cause_braking_too_early():
    """Test probable cause inference for braking too early."""
    metrics = {
        "speed": {"mean_diff": -5.0},
        "throttle": {"mean_diff": 0.0},
        "brake": {"mean_diff": 0.1}
    }
    cause = infer_probable_cause(metrics, "braking")
    assert cause == "braking_too_early"


def test_infer_probable_cause_braking_too_long():
    """Test probable cause inference for braking too long."""
    metrics = {
        "speed": {"mean_diff": -5.0},
        "throttle": {"mean_diff": 0.0},
        "brake": {"mean_diff": 0.2}
    }
    cause = infer_probable_cause(metrics, "braking")
    assert cause == "braking_too_long"


def test_infer_probable_cause_low_minimum_speed():
    """Test probable cause inference for low minimum speed."""
    metrics = {
        "speed": {"mean_diff": -12.0},
        "throttle": {"mean_diff": 0.0},
        "brake": {"mean_diff": 0.0}
    }
    cause = infer_probable_cause(metrics, "entry")
    assert cause == "excessive_entry_speed"


def test_infer_probable_cause_late_throttle():
    """Test probable cause inference for late throttle."""
    metrics = {
        "speed": {"mean_diff": -3.0},
        "throttle": {"mean_diff": -0.15},
        "brake": {"mean_diff": 0.0}
    }
    cause = infer_probable_cause(metrics, "exit")
    assert cause == "late_throttle"


def test_infer_probable_cause_unknown():
    """Test probable cause inference for unknown."""
    metrics = {
        "speed": {"mean_diff": 0.0},
        "throttle": {"mean_diff": 0.0},
        "brake": {"mean_diff": 0.0}
    }
    cause = infer_probable_cause(metrics, "unknown")
    assert cause == "unknown_or_low_confidence"


def test_calculate_confidence_high():
    """Test confidence calculation for high confidence."""
    metrics = {
        "speed": {"mean_diff": -10.0},
        "throttle": {"mean_diff": -0.2},
        "brake": {"mean_diff": 0.1}
    }
    confidence = calculate_confidence(metrics)
    assert confidence == "high"


def test_calculate_confidence_medium():
    """Test confidence calculation for medium confidence."""
    metrics = {
        "speed": {"mean_diff": -10.0},
        "throttle": {},
        "brake": {}
    }
    confidence = calculate_confidence(metrics)
    assert confidence == "medium"


def test_calculate_confidence_low():
    """Test confidence calculation for low confidence."""
    metrics = {
        "speed": {"mean_diff": 0.0},
        "throttle": {},
        "brake": {}
    }
    confidence = calculate_confidence(metrics)
    assert confidence == "low"


def test_build_recommendation_braking_too_early():
    """Test recommendation building for braking too early."""
    metrics = {"speed": {"mean_diff": -5.0}}
    recommendation = build_recommendation("braking", "braking_too_early", metrics)
    assert "frenagem" in recommendation.lower()
    assert "atrase" in recommendation.lower()


def test_build_recommendation_late_throttle():
    """Test recommendation building for late throttle."""
    metrics = {"speed": {"mean_diff": -3.0}}
    recommendation = build_recommendation("exit", "late_throttle", metrics)
    assert "acelerador" in recommendation.lower()
    assert "tarde" in recommendation.lower()


def test_build_recommendation_unknown():
    """Test recommendation building for unknown cause."""
    metrics = {"speed": {"mean_diff": 0.0}}
    recommendation = build_recommendation("unknown", "unknown_or_low_confidence", metrics)
    assert "compare" in recommendation.lower()


def test_generate_top_opportunities_filters_insignificant():
    """Test that insignificant losses (< 0.05s) are filtered out."""
    comparison = {
        "overall": {"metrics": {"speed": {"mean_diff": -1.0}}},
        "sectors": [
            {
                "name": "Sector 1",
                "metrics": {"speed": {"mean_diff": -1.0, "mean_abs_diff": 1.0}}
            },
            {
                "name": "Sector 2",
                "metrics": {"speed": {"mean_diff": -10.0, "mean_abs_diff": 10.0}}
            }
        ]
    }
    opportunities = generate_top_opportunities(comparison, max_opportunities=3)
    # Only Sector 2 should be included (significant loss)
    assert len(opportunities) == 1
    assert opportunities[0]["corner"] == "Sector 2"


def test_generate_top_opportunities_limits_to_max():
    """Test that opportunities are limited to max_opportunities."""
    comparison = {
        "overall": {"metrics": {"speed": {"mean_diff": -10.0}}},
        "sectors": [
            {
                "name": f"Sector {i}",
                "metrics": {"speed": {"mean_diff": -10.0 - i, "mean_abs_diff": 10.0 + i}}
            }
            for i in range(1, 6)
        ]
    }
    opportunities = generate_top_opportunities(comparison, max_opportunities=3)
    assert len(opportunities) == 3


def test_generate_top_opportunities_priority_ordering():
    """Test that opportunities are ordered by time loss (highest first)."""
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
    opportunities = generate_top_opportunities(comparison, max_opportunities=3)
    assert len(opportunities) == 3
    assert opportunities[0]["rank"] == 1
    assert opportunities[0]["corner"] == "Sector 2"
    assert opportunities[1]["rank"] == 2
    assert opportunities[1]["corner"] == "Sector 3"
    assert opportunities[2]["rank"] == 3
    assert opportunities[2]["corner"] == "Sector 1"


def test_generate_top_opportunities_includes_all_required_fields():
    """Test that each opportunity includes all required fields."""
    comparison = {
        "overall": {"metrics": {"speed": {"mean_diff": -10.0}}},
        "sectors": [
            {
                "name": "Sector 1",
                "metrics": {
                    "speed": {"mean_diff": -10.0, "mean_abs_diff": 10.0},
                    "throttle": {"mean_diff": -0.2, "mean_abs_diff": 0.2},
                    "brake": {"mean_diff": 0.1, "mean_abs_diff": 0.1}
                }
            }
        ]
    }
    opportunities = generate_top_opportunities(comparison, max_opportunities=3)
    assert len(opportunities) == 1
    opp = opportunities[0]
    assert "rank" in opp
    assert "corner" in opp
    assert "phase" in opp
    assert "estimated_time_loss" in opp
    assert "confidence" in opp
    assert "probable_cause" in opp
    assert "recommendation" in opp
    assert "evidence" in opp


def test_generate_training_plan_with_opportunities():
    """Test training plan generation with opportunities."""
    opportunities = [
        {
            "rank": 1,
            "corner": "Sector 2",
            "phase": "braking",
            "estimated_time_loss": 0.3,
            "confidence": "high",
            "probable_cause": "braking_too_early",
            "recommendation": "Test recommendation",
            "evidence": {}
        }
    ]
    plan = generate_training_plan(opportunities)
    assert "primary_focus" in plan
    assert "suggested_laps" in plan
    assert "instructions" in plan
    assert "target_metric" in plan
    assert plan["suggested_laps"] == 5
    assert "braking" in plan["primary_focus"]


def test_generate_training_plan_empty_opportunities():
    """Test training plan generation with no opportunities."""
    plan = generate_training_plan([])
    assert plan["primary_focus"] == "Manter consistência"
    assert plan["suggested_laps"] == 5
    assert len(plan["instructions"]) > 0
    assert plan["target_metric"] is None


def test_generate_diagnosis_includes_new_fields():
    """Test that generate_diagnosis includes new structured fields."""
    comparison = {
        "overall": {
            "metrics": {
                "speed": {"mean_diff": -10.0},
                "throttle": {"mean_diff": -0.2},
                "brake": {"mean_diff": 0.1}
            }
        },
        "sectors": [
            {
                "name": "Sector 1",
                "metrics": {
                    "speed": {"mean_diff": -10.0, "mean_abs_diff": 10.0},
                    "throttle": {"mean_diff": -0.2, "mean_abs_diff": 0.2},
                    "brake": {"mean_diff": 0.1, "mean_abs_diff": 0.1}
                }
            }
        ]
    }
    result = generate_diagnosis(comparison)
    assert "top_opportunities" in result
    assert "training_plan" in result
    # Legacy fields should still be present
    assert "priority_items" in result
    assert "likely_driver_issue" in result
    assert "training_focus" in result


def test_generate_diagnosis_top_opportunities_structure():
    """Test that top_opportunities has correct structure."""
    comparison = {
        "overall": {
            "metrics": {
                "speed": {"mean_diff": -10.0},
                "throttle": {"mean_diff": -0.2},
                "brake": {"mean_diff": 0.1}
            }
        },
        "sectors": [
            {
                "name": "Sector 1",
                "metrics": {
                    "speed": {"mean_diff": -10.0, "mean_abs_diff": 10.0},
                    "throttle": {"mean_diff": -0.2, "mean_abs_diff": 0.2},
                    "brake": {"mean_diff": 0.1, "mean_abs_diff": 0.1}
                }
            }
        ]
    }
    result = generate_diagnosis(comparison)
    top_ops = result["top_opportunities"]
    assert len(top_ops) > 0
    opp = top_ops[0]
    assert opp["rank"] == 1
    assert opp["corner"] == "Sector 1"
    assert opp["phase"] in ["braking", "entry", "apex", "exit", "unknown"]
    assert opp["confidence"] in ["high", "medium", "low"]
    assert opp["probable_cause"] in [
        "braking_too_early",
        "braking_too_late",
        "braking_too_long",
        "excessive_entry_speed",
        "low_minimum_speed",
        "late_throttle",
        "partial_throttle_on_exit",
        "poor_exit_speed",
        "unknown_or_low_confidence"
    ]


def test_generate_diagnosis_training_plan_structure():
    """Test that training_plan has correct structure."""
    comparison = {
        "overall": {
            "metrics": {
                "speed": {"mean_diff": -10.0},
                "throttle": {"mean_diff": -0.2},
                "brake": {"mean_diff": 0.1}
            }
        },
        "sectors": [
            {
                "name": "Sector 1",
                "metrics": {
                    "speed": {"mean_diff": -10.0, "mean_abs_diff": 10.0},
                    "throttle": {"mean_diff": -0.2, "mean_abs_diff": 0.2},
                    "brake": {"mean_diff": 0.1, "mean_abs_diff": 0.1}
                }
            }
        ]
    }
    result = generate_diagnosis(comparison)
    plan = result["training_plan"]
    assert "primary_focus" in plan
    assert "suggested_laps" in plan
    assert "instructions" in plan
    assert "target_metric" in plan
    assert isinstance(plan["instructions"], list)
    assert len(plan["instructions"]) > 0
