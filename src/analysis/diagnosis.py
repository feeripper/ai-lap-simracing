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

from typing import Literal


def classify_corner_phase(metrics: dict) -> Literal["braking", "entry", "apex", "exit", "unknown"]:
    """Classify the corner phase based on telemetry metrics.

    Uses available metrics (speed, throttle, brake) to infer which phase
    of the corner the time loss occurred in.

    Args:
        metrics: Dictionary with speed, throttle, brake data for a sector

    Returns:
        Corner phase: braking, entry, apex, exit, or unknown
    """
    speed_data = metrics.get("speed", {})
    throttle_data = metrics.get("throttle", {})
    brake_data = metrics.get("brake", {})

    speed_diff = speed_data.get("mean_diff", 0)
    throttle_diff = throttle_data.get("mean_diff", 0)
    brake_diff = brake_data.get("mean_diff", 0)

    # Braking phase: user brakes more than reference and is slower
    if brake_diff > 0.05 and speed_diff < -2:
        return "braking"

    # Entry phase: user is slower with low throttle
    if speed_diff < -5 and throttle_diff < -0.1:
        return "entry"

    # Apex phase: maximum speed difference (most negative)
    if speed_diff < -10:
        return "apex"

    # Exit phase: throttle difference with moderate speed difference
    if throttle_diff < -0.15 and speed_diff > -5:
        return "exit"

    return "unknown"


def infer_probable_cause(
    metrics: dict,
    phase: Literal["braking", "entry", "apex", "exit", "unknown"]
) -> Literal[
    "braking_too_early",
    "braking_too_late",
    "braking_too_long",
    "excessive_entry_speed",
    "low_minimum_speed",
    "late_throttle",
    "partial_throttle_on_exit",
    "poor_exit_speed",
    "unknown_or_low_confidence",
]:
    """Infer the probable cause of time loss based on metrics and phase.

    Args:
        metrics: Dictionary with speed, throttle, brake data
        phase: Corner phase classification

    Returns:
        Structured probable cause category
    """
    speed_data = metrics.get("speed", {})
    throttle_data = metrics.get("throttle", {})
    brake_data = metrics.get("brake", {})

    speed_diff = speed_data.get("mean_diff", 0)
    throttle_diff = throttle_data.get("mean_diff", 0)
    brake_diff = brake_data.get("mean_diff", 0)

    if phase == "braking":
        if brake_diff > 0.15:
            return "braking_too_long"
        elif brake_diff > 0.05:
            return "braking_too_early"
        else:
            return "unknown_or_low_confidence"

    elif phase == "entry":
        if speed_diff < -10:
            return "excessive_entry_speed"
        elif speed_diff < -5:
            return "low_minimum_speed"
        else:
            return "unknown_or_low_confidence"

    elif phase == "apex":
        if speed_diff < -15:
            return "low_minimum_speed"
        else:
            return "unknown_or_low_confidence"

    elif phase == "exit":
        if throttle_diff < -0.2:
            return "partial_throttle_on_exit"
        elif throttle_diff < -0.1:
            return "late_throttle"
        elif speed_diff < -5:
            return "poor_exit_speed"
        else:
            return "unknown_or_low_confidence"

    return "unknown_or_low_confidence"


def calculate_confidence(metrics: dict) -> Literal["high", "medium", "low"]:
    """Calculate confidence level based on metric availability and consistency.

    Args:
        metrics: Dictionary with speed, throttle, brake data

    Returns:
        Confidence level: high, medium, or low
    """
    speed_data = metrics.get("speed", {})
    throttle_data = metrics.get("throttle", {})
    brake_data = metrics.get("brake", {})

    # Check metric availability
    has_speed = bool(speed_data)
    has_throttle = bool(throttle_data)
    has_brake = bool(brake_data)

    # Check for meaningful differences
    speed_diff = speed_data.get("mean_diff", 0)
    throttle_diff = throttle_data.get("mean_diff", 0)
    brake_diff = brake_data.get("mean_diff", 0)

    has_meaningful_diff = (
        abs(speed_diff) > 1 or abs(throttle_diff) > 0.05 or abs(brake_diff) > 0.05
    )

    # High confidence: multiple metrics with meaningful differences
    if has_speed and has_throttle and has_brake and has_meaningful_diff:
        return "high"

    # Medium confidence: at least speed with meaningful difference
    if has_speed and has_meaningful_diff:
        return "medium"

    # Low confidence: insufficient data
    return "low"


def build_recommendation(
    phase: Literal["braking", "entry", "apex", "exit", "unknown"],
    cause: Literal[
        "braking_too_early",
        "braking_too_late",
        "braking_too_long",
        "excessive_entry_speed",
        "low_minimum_speed",
        "late_throttle",
        "partial_throttle_on_exit",
        "poor_exit_speed",
        "unknown_or_low_confidence",
    ],
    metrics: dict,
) -> str:
    """Build a practical, specific recommendation based on phase and cause.

    Args:
        phase: Corner phase classification
        cause: Probable cause category
        metrics: Dictionary with telemetry data for context

    Returns:
        Practical, actionable recommendation text
    """
    speed_data = metrics.get("speed", {})
    speed_diff = speed_data.get("mean_diff", 0)

    if cause == "braking_too_early":
        return "Você iniciou a frenagem antes da referência. Na próxima sessão, atrase o início da frenagem gradualmente e priorize soltar o freio antes de iniciar a rotação."

    elif cause == "braking_too_long":
        return "Você permaneceu no freio por mais tempo que a referência. Pratique soltar o freio mais cedo e manter velocidade na entrada de curva."

    elif cause == "excessive_entry_speed":
        return "Sua velocidade de entrada está excessiva, causando perda de controle. Pratique frear mais cedo e de forma mais consistente."

    elif cause == "low_minimum_speed":
        return f"Sua velocidade mínima está {abs(speed_diff):.0f} km/h abaixo da referência. Pratique carregar mais velocidade pelo ápice com traçado mais suave."

    elif cause == "late_throttle":
        return "Você iniciou o acelerador tarde após o ápice. Pratique retomar o acelerador mais cedo enquanto o carro ainda está estável."

    elif cause == "partial_throttle_on_exit":
        return "Você não está usando acelerador total na saída. Pratique abrir o acelerador completamente assim que o carro estiver estável na saída."

    elif cause == "poor_exit_speed":
        return f"Sua velocidade de saída está {abs(speed_diff):.0f} km/h abaixo da referência. Pratique aceleração mais agressiva na saída de curva."

    else:
        return "Compare sua telemetria com a referência para identificar o padrão específico de perda de tempo."


def generate_top_opportunities(comparison: dict, max_opportunities: int = 3) -> list[dict]:
    """Generate top 3 time loss opportunities with structured coaching output.

    Args:
        comparison: Dictionary returned by compare_laps
        max_opportunities: Maximum number of opportunities to return (default: 3)

    Returns:
        List of top opportunities with rank, corner, phase, time loss, confidence,
        probable cause, recommendation, and evidence metrics.
    """
    time_loss = estimate_time_loss_from_speed(comparison)

    # Filter out insignificant losses (< 0.05s)
    significant_losses = [
        s for s in time_loss["sectors"]
        if s["time_loss_seconds"] >= 0.05
    ]

    # Sort by time loss (highest first)
    sorted_losses = sorted(
        significant_losses,
        key=lambda x: x["time_loss_seconds"],
        reverse=True
    )

    # Limit to max_opportunities
    top_losses = sorted_losses[:max_opportunities]

    opportunities = []
    for rank, loss_area in enumerate(top_losses, start=1):
        sector_name = loss_area["name"]
        loss_seconds = loss_area["time_loss_seconds"]

        # Get sector-specific metrics
        sector_metrics = {}
        for sector in comparison.get("sectors", []):
            if sector.get("name") == sector_name:
                sector_metrics = sector.get("metrics", {})
                break

        # Classify phase, cause, confidence
        phase = classify_corner_phase(sector_metrics)
        cause = infer_probable_cause(sector_metrics, phase)
        confidence = calculate_confidence(sector_metrics)

        # Build recommendation
        recommendation = build_recommendation(phase, cause, sector_metrics)

        opportunities.append({
            "rank": rank,
            "corner": sector_name,
            "phase": phase,
            "estimated_time_loss": round(loss_seconds, 3),
            "confidence": confidence,
            "probable_cause": cause,
            "recommendation": recommendation,
            "evidence": sector_metrics
        })

    return opportunities


def generate_training_plan(opportunities: list[dict]) -> dict:
    """Generate a training plan based on top opportunities.

    Args:
        opportunities: List of top opportunities from generate_top_opportunities

    Returns:
        Training plan with primary focus, suggested laps, and instructions.
    """
    if not opportunities:
        return {
            "primary_focus": "Manter consistência",
            "suggested_laps": 5,
            "instructions": [
                "Continue praticando para manter consistência.",
                "Compare sua telemetria com a referência regularmente."
            ],
            "target_metric": None
        }

    # Primary focus is the top opportunity
    top_opportunity = opportunities[0]
    primary_focus = f"{top_opportunity['phase']} em {top_opportunity['corner']}"

    # Build instructions based on opportunities
    instructions = []
    for opp in opportunities:
        instructions.append(f"Prioridade {opp['rank']}: {opp['recommendation']}")

    # Add general guidance
    instructions.append(
        "Não tente corrigir tudo simultaneamente. Foque primeiro na prioridade 1."
    )
    instructions.append(
        "Execute 5 voltas focadas apenas no problema principal antes de avançar."
    )

    # Calculate target metric (aim to reduce top loss by 30%)
    top_loss = top_opportunity["estimated_time_loss"]
    target_reduction = round(top_loss * 0.3, 3)
    target_metric = f"Reduzir perda em {top_opportunity['corner']} em {target_reduction:.3f}s"

    return {
        "primary_focus": primary_focus,
        "suggested_laps": 5,
        "instructions": instructions,
        "target_metric": target_metric
    }


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
            "priority_items": [...],  # Legacy format for backward compatibility
            "likely_driver_issue": "...",
            "training_focus": "...",
            "top_opportunities": [...],  # New structured format
            "training_plan": {...}      # New training plan
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

    # Build priority items (top 3 loss areas) - legacy format for backward compatibility
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

    # Generate new structured output
    top_opportunities = generate_top_opportunities(comparison, max_opportunities=3)
    training_plan = generate_training_plan(top_opportunities)

    return {
        "overall_lap_delta_seconds": overall_delta,
        "summary": summary,
        "priority_items": priority_items,  # Legacy format
        "likely_driver_issue": likely_issue,
        "training_focus": training_focus,
        "top_opportunities": top_opportunities,  # New structured format
        "training_plan": training_plan  # New training plan
    }
