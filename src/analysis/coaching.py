"""Coaching analysis focused on time loss and training recommendations.

This module extends the existing comparison/insight flow with coaching-specific
output: where the driver lost time, strongest loss areas, probable driving issues,
and recommended training actions.
"""

from __future__ import annotations

from typing import Optional


def estimate_time_loss_from_speed(
    comparison: dict, distance_column: str = "lap_dist_pct"
) -> dict:
    """Estimate time loss by sector from speed differences.

    Since Garage61 CSVs may not include explicit lap time, we estimate time loss
    from speed differences: slower speed in a segment typically means time lost.

    Args:
        comparison: Dictionary returned by compare_laps with sectors
        distance_column: Name of the distance column

    Returns:
        Dictionary with time loss estimates by sector:
        {
            "total_time_loss_seconds": 2.5,
            "sectors": [
                {"name": "Sector 1", "time_loss_seconds": 0.8, "severity": "high"},
                ...
            ]
        }
    """
    sectors = comparison.get("sectors", [])
    if not sectors:
        return {"total_time_loss_seconds": 0.0, "sectors": []}

    sector_losses = []
    total_loss = 0.0

    for sector in sectors:
        sector_name = sector.get("name", "Unknown")
        metrics = sector.get("metrics", {})
        speed_data = metrics.get("speed", {})

        if not speed_data:
            sector_losses.append({
                "name": sector_name,
                "time_loss_seconds": 0.0,
                "severity": "none"
            })
            continue

        mean_diff = speed_data.get("mean_diff", 0)
        mean_abs_diff = speed_data.get("mean_abs_diff", 0)

        # Negative mean_diff means user is slower than reference
        # Estimate time loss: if consistently slower, lose time
        if mean_diff < 0:
            # Rough estimate: 1 km/h slower over 25% of lap ≈ 0.2-0.3s loss
            # This is a heuristic for coaching, not precise timing
            estimated_loss = abs(mean_diff) * 0.025
        else:
            estimated_loss = 0.0

        total_loss += estimated_loss

        # Determine severity based on estimated loss
        if estimated_loss >= 0.5:
            severity = "high"
        elif estimated_loss >= 0.2:
            severity = "medium"
        else:
            severity = "low"

        sector_losses.append({
            "name": sector_name,
            "time_loss_seconds": round(estimated_loss, 3),
            "severity": severity
        })

    return {
        "total_time_loss_seconds": round(total_loss, 3),
        "sectors": sector_losses
    }


def identify_strongest_loss_areas(time_loss: dict) -> list[dict]:
    """Identify the sectors with the highest time loss.

    Args:
        time_loss: Dictionary returned by estimate_time_loss_from_speed

    Returns:
        List of sectors sorted by time loss (highest first):
        [
            {"name": "Sector 1", "time_loss_seconds": 0.8, "severity": "high"},
            ...
        ]
    """
    sectors = time_loss.get("sectors", [])
    # Sort by time loss descending
    sorted_sectors = sorted(
        [s for s in sectors if s["time_loss_seconds"] > 0],
        key=lambda x: x["time_loss_seconds"],
        reverse=True
    )
    return sorted_sectors


def infer_driving_issue(comparison: dict, time_loss: dict) -> str:
    """Infer the most probable driving issue from telemetry and time loss.

    Args:
        comparison: Dictionary returned by compare_laps
        time_loss: Dictionary returned by estimate_time_loss_from_speed

    Returns:
        Human-readable description of the probable driving issue.
    """
    overall_metrics = comparison.get("overall", {}).get("metrics", {})
    speed_data = overall_metrics.get("speed", {})
    throttle_data = overall_metrics.get("throttle", {})
    brake_data = overall_metrics.get("brake", {})

    speed_mean_diff = speed_data.get("mean_diff", 0)
    throttle_mean_diff = throttle_data.get("mean_diff", 0)
    brake_mean_diff = brake_data.get("mean_diff", 0)

    # Analyze patterns
    issues = []

    if speed_mean_diff < -5:
        issues.append("velocidade consistentemente abaixo da referência")

    if throttle_mean_diff < -0.1:
        issues.append("uso de acelerador abaixo da referência (aceleração tardia ou saída fraca)")

    if brake_mean_diff > 0.1:
        issues.append("uso excessivo de freio (frenagem prolongada ou desnecessária)")

    if not issues:
        return "Sua volta está muito próxima da referência. Bom trabalho!"

    # Prioritize speed loss
    if speed_mean_diff < -5:
        return f"Você está perdendo tempo principalmente por {issues[0]}. "
    elif throttle_mean_diff < -0.1:
        return f"Você está perdendo tempo principalmente por {issues[0]}. "
    elif brake_mean_diff > 0.1:
        return f"Você está perdendo tempo principalmente por {issues[0]}. "
    else:
        return f"Você está perdendo tempo por {', '.join(issues)}."


def recommend_training_action(
    comparison: dict, time_loss: dict, driving_issue: str
) -> str:
    """Recommend a specific training action based on the analysis.

    Args:
        comparison: Dictionary returned by compare_laps
        time_loss: Dictionary returned by estimate_time_loss_from_speed
        driving_issue: String describing the probable driving issue

    Returns:
        Human-readable training recommendation.
    """
    strongest_losses = identify_strongest_loss_areas(time_loss)

    if not strongest_losses:
        return "Continue praticando para manter consistência."

    top_loss = strongest_losses[0]
    sector_name = top_loss["name"]

    overall_metrics = comparison.get("overall", {}).get("metrics", {})
    speed_data = overall_metrics.get("speed", {})
    throttle_data = overall_metrics.get("throttle", {})
    brake_data = overall_metrics.get("brake", {})

    speed_mean_diff = speed_data.get("mean_diff", 0)
    throttle_mean_diff = throttle_data.get("mean_diff", 0)
    brake_mean_diff = brake_data.get("mean_diff", 0)

    # Generate specific training recommendation
    if speed_mean_diff < -5:
        if throttle_mean_diff < -0.1:
            return f"Treine aceleração mais agressiva em {sector_name}. "
            "Foque em abrir o acelerador mais cedo na saída de curva."
        else:
            return f"Treine traçado e velocidade em {sector_name}. "
            "Revise se está levando a curva muito larga ou freando demais."

    elif brake_mean_diff > 0.1:
        return f"Treine pontos de frenagem em {sector_name}. "
        "Pratique freiar mais tarde e de forma mais decisiva."

    elif throttle_mean_diff < -0.1:
        return f"Treine aceleração em {sector_name}. "
        "Foque em manter o acelerador aberto por mais tempo."

    else:
        return f"Revise sua condução em {sector_name}. "
        "Compare sua telemetria com a referência para identificar o padrão."


def generate_coaching_analysis(comparison: dict) -> dict:
    """Generate complete coaching analysis from comparison result.

    This is the main entry point for coaching-specific output. It extends the
    existing comparison with time loss estimates, strongest loss areas, probable
    driving issues, and training recommendations.

    Args:
        comparison: Dictionary returned by compare_laps

    Returns:
        Dictionary with coaching-specific output:
        {
            "time_loss": {...},
            "strongest_loss_areas": [...],
            "driving_issue": "...",
            "training_recommendation": "..."
        }
    """
    time_loss = estimate_time_loss_from_speed(comparison)
    strongest_losses = identify_strongest_loss_areas(time_loss)
    driving_issue = infer_driving_issue(comparison, time_loss)
    training_recommendation = recommend_training_action(
        comparison, time_loss, driving_issue
    )

    return {
        "time_loss": time_loss,
        "strongest_loss_areas": strongest_losses,
        "driving_issue": driving_issue,
        "training_recommendation": training_recommendation
    }


def generate_diagnosis(comparison: dict) -> dict:
    """Generate driver-friendly coaching diagnosis with clear priority ordering.

    This is the AI simracing coach output that tells the driver:
    - Where they are losing time
    - Why it's probably happening
    - What to train next
    - In priority order (priority 1, priority 2, priority 3)

    Args:
        comparison: Dictionary returned by compare_laps

    Returns:
        Dictionary with driver-friendly diagnosis:
        {
            "overall_lap_delta_seconds": 2.5,
            "summary": "You are losing 2.5s compared to the reference lap.",
            "priority_items": [
                {
                    "priority": 1,
                    "location": "Sector 2",
                    "time_loss_seconds": 0.8,
                    "why": "You are 12 km/h slower through this sector.",
                    "what_to_train": "Practice later braking and carry more speed through the corner."
                },
                ...
            ],
            "likely_driver_issue": "...",
            "training_focus": "..."
        }
    """
    time_loss = estimate_time_loss_from_speed(comparison)
    strongest_losses = identify_strongest_loss_areas(time_loss)
    driving_issue = infer_driving_issue(comparison, time_loss)
    training_recommendation = recommend_training_action(
        comparison, time_loss, driving_issue
    )

    overall_delta = time_loss["total_time_loss_seconds"]

    # Generate summary
    if overall_delta > 0:
        summary = f"Você está perdendo {overall_delta:.2f}s em relação à volta de referência."
    else:
        summary = "Sua volta está muito próxima da referência. Bom trabalho!"

    # Build priority items (top 3 loss areas)
    priority_items = []
    for idx, loss_area in enumerate(strongest_losses[:3], start=1):
        sector_name = loss_area["name"]
        loss_seconds = loss_area["time_loss_seconds"]
        severity = loss_area["severity"]

        # Get sector-specific metrics for "why" explanation
        sector_metrics = {}
        for sector in comparison.get("sectors", []):
            if sector.get("name") == sector_name:
                sector_metrics = sector.get("metrics", {})
                break

        # Generate "why" explanation
        speed_data = sector_metrics.get("speed", {})
        speed_diff = speed_data.get("mean_diff", 0)

        if speed_diff < -5:
            why = f"Você está {abs(speed_diff):.0f} km/h mais lento neste setor."
        elif speed_diff < -2:
            why = f"Você está {abs(speed_diff):.0f} km/h mais lento neste setor."
        elif speed_diff < 0:
            why = "Você está levemente mais lento neste setor."
        else:
            # Check other metrics
            throttle_data = sector_metrics.get("throttle", {})
            brake_data = sector_metrics.get("brake", {})
            throttle_diff = throttle_data.get("mean_diff", 0)
            brake_diff = brake_data.get("mean_diff", 0)

            if throttle_diff < -0.1:
                why = "Você está usando menos acelerador que a referência."
            elif brake_diff > 0.1:
                why = "Você está freando mais que a referência."
            else:
                why = "Sua telemetria difere da referência neste setor."

        # Generate "what to train" based on the issue
        if speed_diff < -5:
            if throttle_diff < -0.1:
                what_to_train = "Pratique aceleração mais agressiva na saída de curva."
            else:
                what_to_train = "Pratique traçado e frenagem para carregar mais velocidade."
        elif brake_diff > 0.1:
            what_to_train = "Pratique freiar mais tarde e de forma mais decisiva."
        elif throttle_diff < -0.1:
            what_to_train = "Pratique manter o acelerador aberto por mais tempo."
        else:
            what_to_train = "Compare sua telemetria com a referência para identificar o padrão."

        priority_items.append({
            "priority": idx,
            "location": sector_name,
            "time_loss_seconds": loss_seconds,
            "severity": severity,
            "why": why,
            "what_to_train": what_to_train
        })

    # Fallback for sector names if unavailable
    if not priority_items and overall_delta > 0:
        priority_items.append({
            "priority": 1,
            "location": "Setor desconhecido",
            "time_loss_seconds": overall_delta,
            "severity": "medium",
            "why": "Análise geral indica perda de tempo.",
            "what_to_train": training_recommendation
        })

    return {
        "overall_lap_delta_seconds": overall_delta,
        "summary": summary,
        "priority_items": priority_items,
        "likely_driver_issue": driving_issue,
        "training_focus": training_recommendation
    }
