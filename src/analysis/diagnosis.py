"""AI simracing coach diagnosis layer.

This module converts telemetry comparison output into driver-friendly coaching
guidance that tells the driver:
- where they are losing time
- why it is probably happening
- what to train next

The output is structured with clear priority ordering (priority 1, 2, 3) and
plain language suitable for the frontend.
"""

from __future__ import annotations


def estimate_time_loss_from_speed(comparison: dict) -> dict:
    """Estimate time loss by sector from speed differences.

    Since CSVs may not include explicit lap time, we estimate time loss
    from speed differences: slower speed in a segment typically means time lost.

    Args:
        comparison: Dictionary returned by compare_laps with sectors

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

    # Fallback: if no sectors, use overall metrics to estimate full lap time loss
    if not sectors:
        overall_metrics = comparison.get("overall", {}).get("metrics", {})
        speed_data = overall_metrics.get("speed", {})
        mean_diff = speed_data.get("mean_diff", 0)

        if mean_diff < 0:
            # Rough estimate: 1 km/h slower over full lap ≈ 0.1s loss
            estimated_loss = abs(mean_diff) * 0.1

            # Determine severity based on estimated loss
            if estimated_loss >= 0.5:
                severity = "high"
            elif estimated_loss >= 0.2:
                severity = "medium"
            else:
                severity = "low"

            return {
                "total_time_loss_seconds": round(estimated_loss, 3),
                "sectors": [
                    {
                        "name": "Full lap",
                        "time_loss_seconds": round(estimated_loss, 3),
                        "severity": severity
                    }
                ]
            }
        else:
            # No speed loss detected
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

        # Negative mean_diff means user is slower than reference
        # Estimate time loss: if consistently slower, lose time
        if mean_diff < 0:
            # Rough estimate: 1 km/h slower over 25% of lap ≈ 0.2-0.3s loss
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
    overall_delta = time_loss["total_time_loss_seconds"]

    # Sort sectors by time loss (highest first)
    sorted_sectors = sorted(
        [s for s in time_loss["sectors"] if s["time_loss_seconds"] > 0],
        key=lambda x: x["time_loss_seconds"],
        reverse=True
    )

    # Generate summary
    if overall_delta > 0:
        summary = f"Você está perdendo {overall_delta:.2f}s em relação à volta de referência."
    else:
        summary = "Sua volta está muito próxima da referência. Bom trabalho!"

    # Build priority items (top 3 loss areas)
    priority_items = []
    for idx, loss_area in enumerate(sorted_sectors[:3], start=1):
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
        throttle_data = sector_metrics.get("throttle", {})
        brake_data = sector_metrics.get("brake", {})
        throttle_diff = throttle_data.get("mean_diff", 0)
        brake_diff = brake_data.get("mean_diff", 0)

        if speed_diff < -5:
            why = f"Você está {abs(speed_diff):.0f} km/h mais lento neste setor."
        elif speed_diff < -2:
            why = f"Você está {abs(speed_diff):.0f} km/h mais lento neste setor."
        elif speed_diff < 0:
            why = "Você está levemente mais lento neste setor."
        elif throttle_diff < -0.1:
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
            "what_to_train": "Revise sua condução geral e compare com a referência."
        })

    # Determine likely driver issue from overall metrics
    overall_metrics = comparison.get("overall", {}).get("metrics", {})
    speed_mean_diff = overall_metrics.get("speed", {}).get("mean_diff", 0)
    throttle_mean_diff = overall_metrics.get("throttle", {}).get("mean_diff", 0)
    brake_mean_diff = overall_metrics.get("brake", {}).get("mean_diff", 0)

    if speed_mean_diff < -5:
        likely_issue = "Velocidade consistentemente abaixo da referência"
    elif throttle_mean_diff < -0.1:
        likely_issue = "Uso de acelerador abaixo da referência (aceleração tardia)"
    elif brake_mean_diff > 0.1:
        likely_issue = "Uso excessivo de freio (frenagem prolongada)"
    elif overall_delta > 0:
        likely_issue = "Perda de tempo em múltiplos setores"
    else:
        likely_issue = "Nenhum problema significativo identificado"

    # Generate training focus
    if speed_mean_diff < -5:
        training_focus = "Foque em carregar mais velocidade pelos setores."
    elif brake_mean_diff > 0.1:
        training_focus = "Foque em pontos de frenagem mais tardios."
    elif throttle_mean_diff < -0.1:
        training_focus = "Foque em aceleração mais agressiva na saída de curvas."
    elif overall_delta > 0:
        training_focus = "Revise os setores com maior perda de tempo."
    else:
        training_focus = "Continue praticando para manter consistência."

    return {
        "overall_lap_delta_seconds": overall_delta,
        "summary": summary,
        "priority_items": priority_items,
        "likely_driver_issue": likely_issue,
        "training_focus": training_focus
    }
