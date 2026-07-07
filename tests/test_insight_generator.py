"""Unit tests for insight generator."""

from __future__ import annotations

import pytest

from src.analysis.insight_generator import generate_insights


def test_generate_insights_basic_speed_loss():
    """Test basic insight generation with speed loss."""
    comparison = {
        "overall": {
            "comparable_columns": ["speed"],
            "num_points": 101,
            "metrics": {
                "speed": {
                    "mean_diff": -8.5,
                    "min_diff": -20.0,
                    "max_diff": -2.0,
                    "mean_abs_diff": 8.5
                }
            }
        },
        "sectors": []
    }

    result = generate_insights(comparison)

    # Validate structure
    assert "summary" in result
    assert "priority" in result
    assert "recommendations" in result
    assert "sector_insights" in result

    # Validate priority is speed
    assert result["priority"] == "speed"

    # Validate recommendation for speed
    assert len(result["recommendations"]) == 1
    rec = result["recommendations"][0]
    assert rec["metric"] == "speed"
    assert "velocidade" in rec["title"].lower()
    assert "mais lento" in rec["message"].lower()
    assert rec["severity"] == "medium"  # 8.5 is between 5 and 15
    assert rec["evidence"]["mean_diff"] == -8.5
    assert rec["evidence"]["mean_abs_diff"] == 8.5


def test_generate_insights_throttle_loss():
    """Test insight generation with throttle loss."""
    comparison = {
        "overall": {
            "comparable_columns": ["throttle"],
            "num_points": 101,
            "metrics": {
                "throttle": {
                    "mean_diff": -0.1,
                    "min_diff": -0.3,
                    "max_diff": 0.0,
                    "mean_abs_diff": 0.1
                }
            }
        },
        "sectors": []
    }

    result = generate_insights(comparison)

    # Validate priority is throttle
    assert result["priority"] == "throttle"

    # Validate recommendation for throttle
    assert len(result["recommendations"]) == 1
    rec = result["recommendations"][0]
    assert rec["metric"] == "throttle"
    assert "acelerador" in rec["title"].lower()
    assert "menos acelerador" in rec["message"].lower()
    assert "aceleração tardia" in rec["message"].lower() or "saída de curva" in rec["message"].lower()
    assert rec["severity"] == "medium"  # 0.1 is between 0.05 and 0.15


def test_generate_insights_brake_excess():
    """Test insight generation with brake excess."""
    comparison = {
        "overall": {
            "comparable_columns": ["brake"],
            "num_points": 101,
            "metrics": {
                "brake": {
                    "mean_diff": 0.2,
                    "min_diff": 0.0,
                    "max_diff": 0.5,
                    "mean_abs_diff": 0.2
                }
            }
        },
        "sectors": []
    }

    result = generate_insights(comparison)

    # Validate priority is brake
    assert result["priority"] == "brake"

    # Validate recommendation for brake
    assert len(result["recommendations"]) == 1
    rec = result["recommendations"][0]
    assert rec["metric"] == "brake"
    assert "freio" in rec["title"].lower()
    assert "mais freio" in rec["message"].lower()
    assert "excesso de freio" in rec["message"].lower() or "frenagem prolongada" in rec["message"].lower()
    assert rec["severity"] == "high"  # 0.2 is > 0.15


def test_generate_insights_steering_difference():
    """Test insight generation with steering difference."""
    comparison = {
        "overall": {
            "comparable_columns": ["steering"],
            "num_points": 101,
            "metrics": {
                "steering": {
                    "mean_diff": 2.0,
                    "min_diff": -5.0,
                    "max_diff": 10.0,
                    "mean_abs_diff": 8.0
                }
            }
        },
        "sectors": []
    }

    result = generate_insights(comparison)

    # Validate priority is steering
    assert result["priority"] == "steering"

    # Validate recommendation for steering
    assert len(result["recommendations"]) == 1
    rec = result["recommendations"][0]
    assert rec["metric"] == "steering"
    assert "volante" in rec["title"].lower()
    assert "volante" in rec["message"].lower()
    assert "traçado" in rec["message"].lower() or "correções" in rec["message"].lower()
    assert rec["severity"] == "medium"  # 8.0 is between 5 and 15


def test_generate_insights_sector_insights():
    """Test sector insights generation."""
    comparison = {
        "overall": {
            "comparable_columns": ["speed"],
            "num_points": 101,
            "metrics": {
                "speed": {
                    "mean_diff": -5.0,
                    "min_diff": -10.0,
                    "max_diff": 0.0,
                    "mean_abs_diff": 5.0
                }
            }
        },
        "sectors": [
            {
                "name": "Sector 1",
                "start_pct": 0,
                "end_pct": 25,
                "metrics": {
                    "speed": {
                        "mean_diff": -6.2,
                        "mean_abs_diff": 6.2
                    }
                }
            },
            {
                "name": "Sector 2",
                "start_pct": 25,
                "end_pct": 50,
                "metrics": {}
            }
        ]
    }

    result = generate_insights(comparison)

    # Validate sector insights
    assert len(result["sector_insights"]) == 1
    sector_insight = result["sector_insights"][0]
    assert sector_insight["sector"] == "Sector 1"
    assert sector_insight["main_metric"] == "speed"
    assert "abaixo" in sector_insight["message"].lower()
    assert sector_insight["severity"] == "medium"
    assert sector_insight["evidence"]["mean_diff"] == -6.2
    assert sector_insight["evidence"]["mean_abs_diff"] == 6.2


def test_generate_insights_limits_recommendations_to_five():
    """Test that recommendations are limited to 5."""
    comparison = {
        "overall": {
            "comparable_columns": ["speed", "throttle", "brake", "steering", "gear"],
            "num_points": 101,
            "metrics": {
                "speed": {"mean_diff": -10.0, "min_diff": -20.0, "max_diff": 0.0, "mean_abs_diff": 10.0},
                "throttle": {"mean_diff": -0.1, "min_diff": -0.2, "max_diff": 0.0, "mean_abs_diff": 0.1},
                "brake": {"mean_diff": 0.1, "min_diff": 0.0, "max_diff": 0.2, "mean_abs_diff": 0.1},
                "steering": {"mean_diff": 5.0, "min_diff": -5.0, "max_diff": 10.0, "mean_abs_diff": 6.0},
                "gear": {"mean_diff": 0.5, "min_diff": 0.0, "max_diff": 1.0, "mean_abs_diff": 0.5}
            }
        },
        "sectors": []
    }

    result = generate_insights(comparison)

    # Should have exactly 5 recommendations
    assert len(result["recommendations"]) == 5


def test_generate_insights_empty_comparison():
    """Test error when comparison is empty."""
    with pytest.raises(ValueError) as exc_info:
        generate_insights({})

    assert "comparison is empty" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        generate_insights(None)

    assert "comparison is empty" in str(exc_info.value)


def test_generate_insights_missing_overall():
    """Test error when overall section is missing."""
    comparison = {
        "sectors": []
    }

    with pytest.raises(ValueError) as exc_info:
        generate_insights(comparison)

    assert "overall" in str(exc_info.value)


def test_generate_insights_no_metrics():
    """Test error when no metrics are available."""
    comparison = {
        "overall": {
            "comparable_columns": [],
            "num_points": 101,
            "metrics": {}
        },
        "sectors": []
    }

    with pytest.raises(ValueError) as exc_info:
        generate_insights(comparison)

    assert "no metrics" in str(exc_info.value)


def test_generate_insights_missing_sectors_does_not_break():
    """Test that missing sectors does not break the function."""
    comparison = {
        "overall": {
            "comparable_columns": ["speed"],
            "num_points": 101,
            "metrics": {
                "speed": {
                    "mean_diff": -5.0,
                    "min_diff": -10.0,
                    "max_diff": 0.0,
                    "mean_abs_diff": 5.0
                }
            }
        }
    }

    result = generate_insights(comparison)

    # Should return empty sector_insights
    assert result["sector_insights"] == []

    # Should still generate recommendations
    assert len(result["recommendations"]) == 1
    assert result["recommendations"][0]["metric"] == "speed"


def test_generate_insights_priority_skips_low_severity_when_medium_exists():
    """Test that priority skips low severity when medium severity exists."""
    comparison = {
        "overall": {
            "comparable_columns": ["speed", "throttle"],
            "num_points": 101,
            "metrics": {
                "speed": {
                    "mean_diff": -3.0,
                    "min_diff": -5.0,
                    "max_diff": -1.0,
                    "mean_abs_diff": 3.0  # low severity (<= 5)
                },
                "throttle": {
                    "mean_diff": -0.1,
                    "min_diff": -0.2,
                    "max_diff": 0.0,
                    "mean_abs_diff": 0.1  # medium severity (> 0.05 and <= 0.15)
                }
            }
        },
        "sectors": []
    }

    result = generate_insights(comparison)

    # Priority should be throttle (medium severity) not speed (low severity)
    assert result["priority"] == "throttle"

    # Both recommendations should be generated
    assert len(result["recommendations"]) == 2
    assert result["recommendations"][0]["metric"] == "speed"
    assert result["recommendations"][0]["severity"] == "low"
    assert result["recommendations"][1]["metric"] == "throttle"
    assert result["recommendations"][1]["severity"] == "medium"


def test_generate_insights_priority_uses_first_low_when_only_low_exists():
    """Test that priority uses first low severity when only low severity exists."""
    comparison = {
        "overall": {
            "comparable_columns": ["speed", "throttle"],
            "num_points": 101,
            "metrics": {
                "speed": {
                    "mean_diff": -3.0,
                    "min_diff": -5.0,
                    "max_diff": -1.0,
                    "mean_abs_diff": 3.0  # low severity
                },
                "throttle": {
                    "mean_diff": -0.03,
                    "min_diff": -0.05,
                    "max_diff": 0.0,
                    "mean_abs_diff": 0.03  # low severity (<= 0.05)
                }
            }
        },
        "sectors": []
    }

    result = generate_insights(comparison)

    # Priority should be speed (first recommendation with low severity)
    assert result["priority"] == "speed"

    # Both recommendations should be generated
    assert len(result["recommendations"]) == 2
    assert result["recommendations"][0]["metric"] == "speed"
    assert result["recommendations"][0]["severity"] == "low"
    assert result["recommendations"][1]["metric"] == "throttle"
    assert result["recommendations"][1]["severity"] == "low"
