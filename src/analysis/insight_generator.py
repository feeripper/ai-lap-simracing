"""Generate coaching insights from lap comparison results."""

from __future__ import annotations


def generate_insights(comparison: dict) -> dict:
    """Generate coaching insights from lap comparison results.

    This function takes the comparison result from compare_laps and generates
    human-readable feedback about the user's driving performance.

    Args:
        comparison: Dictionary returned by compare_laps with overall metrics and sectors

    Returns:
        A dictionary containing:
        {
            "summary": "Brief summary of the comparison",
            "priority": "speed" | "throttle" | "brake" | "steering" | "gear" | "general",
            "recommendations": [
                {
                    "title": "Title of recommendation",
                    "message": "Detailed message",
                    "metric": "speed",
                    "severity": "low" | "medium" | "high",
                    "evidence": {"mean_diff": -8.5, "mean_abs_diff": 8.5}
                }
            ],
            "sector_insights": [
                {
                    "sector": "Sector 1",
                    "message": "Sector-specific message",
                    "main_metric": "speed",
                    "severity": "medium",
                    "evidence": {"mean_diff": -6.2, "mean_abs_diff": 6.2}
                }
            ]
        }

    Raises:
        ValueError: If comparison is empty, missing overall, or has no metrics
    """
    # Validate comparison
    if not comparison:
        raise ValueError("comparison is empty")

    if "overall" not in comparison:
        raise ValueError("comparison missing 'overall' section")

    overall = comparison["overall"]
    if "metrics" not in overall or not overall["metrics"]:
        raise ValueError("comparison has no metrics")

    metrics = overall["metrics"]
    comparable_columns = overall.get("comparable_columns", [])

    # Determine severity based on mean_abs_diff
    def get_severity(metric: str, mean_abs_diff: float) -> str:
        """Determine severity level for a metric."""
        if metric in ["throttle", "brake"]:
            # Smaller thresholds for 0-1 range values
            if mean_abs_diff > 0 and mean_abs_diff <= 0.05:
                return "low"
            elif mean_abs_diff > 0.05 and mean_abs_diff <= 0.15:
                return "medium"
            elif mean_abs_diff > 0.15:
                return "high"
        else:
            # Standard thresholds for speed, steering, gear
            if mean_abs_diff > 0 and mean_abs_diff <= 5:
                return "low"
            elif mean_abs_diff > 5 and mean_abs_diff <= 15:
                return "medium"
            elif mean_abs_diff > 15:
                return "high"
        return "low"

    # Generate recommendations for each metric
    recommendations = []
    priority_order = ["speed", "throttle", "brake", "steering", "gear"]

    for metric in priority_order:
        if metric not in metrics:
            continue

        metric_data = metrics[metric]
        mean_diff = metric_data["mean_diff"]
        mean_abs_diff = metric_data["mean_abs_diff"]

        if mean_abs_diff == 0:
            continue

        severity = get_severity(metric, mean_abs_diff)

        # Generate message based on metric and direction
        if metric == "speed":
            if mean_diff < 0:
                title = "Melhorar velocidade média"
                message = "Você está mais lento que a referência em média."
            else:
                title = "Velocidade acima da referência"
                message = "Sua velocidade está acima da referência em média."

        elif metric == "throttle":
            if mean_diff < 0:
                title = "Melhorar uso de acelerador"
                message = "Você está usando menos acelerador que a referência. Isso pode indicar aceleração tardia ou saída de curva fraca."
            else:
                title = "Uso de acelerador acima da referência"
                message = "Você está usando mais acelerador que a referência."

        elif metric == "brake":
            if mean_diff > 0:
                title = "Revisar uso de freio"
                message = "Você está usando mais freio que a referência. Isso pode indicar excesso de freio ou frenagem prolongada."
            else:
                title = "Uso de freio abaixo da referência"
                message = "Você está usando menos freio que a referência."

        elif metric == "steering":
            title = "Revisar uso de volante"
            message = "Seu uso de volante difere da referência. Isso pode indicar diferença de traçado ou correções excessivas."

        elif metric == "gear":
            title = "Revisar seleção de marcha"
            message = "Sua seleção de marcha difere da referência. Revise se está trocando marcha no momento correto."

        recommendations.append({
            "title": title,
            "message": message,
            "metric": metric,
            "severity": severity,
            "evidence": {
                "mean_diff": mean_diff,
                "mean_abs_diff": mean_abs_diff
            }
        })

    # Limit to 5 recommendations
    recommendations = recommendations[:5]

    # Determine priority: first recommendation with medium or high severity
    priority = "general"
    for rec in recommendations:
        if rec["severity"] in ["medium", "high"]:
            priority = rec["metric"]
            break
    else:
        # If all are low, use the first recommendation's metric
        if recommendations:
            priority = recommendations[0]["metric"]

    # Generate summary
    if recommendations:
        summary = f"Comparação completa com {len(recommendations)} recomendações para melhorar sua volta."
    else:
        summary = "Sua volta está muito próxima da referência. Bom trabalho!"

    # Generate sector insights
    sector_insights = []
    if "sectors" in comparison:
        for sector in comparison["sectors"]:
            sector_name = sector.get("name", "Unknown")
            sector_metrics = sector.get("metrics", {})

            if not sector_metrics:
                continue

            # Find the metric with highest mean_abs_diff in this sector
            main_metric = None
            max_diff = 0
            for metric, metric_data in sector_metrics.items():
                mean_abs_diff = metric_data.get("mean_abs_diff", 0)
                if mean_abs_diff > max_diff:
                    max_diff = mean_abs_diff
                    main_metric = metric

            if main_metric and max_diff > 0:
                severity = get_severity(main_metric, max_diff)
                mean_diff = sector_metrics[main_metric].get("mean_diff", 0)

                if main_metric == "speed":
                    message = f"No {sector_name}, sua velocidade média ficou {'abaixo' if mean_diff < 0 else 'acima'} da referência."
                elif main_metric == "throttle":
                    message = f"No {sector_name}, seu uso de acelerador ficou {'abaixo' if mean_diff < 0 else 'acima'} da referência."
                elif main_metric == "brake":
                    message = f"No {sector_name}, seu uso de freio ficou {'acima' if mean_diff > 0 else 'abaixo'} da referência."
                elif main_metric == "steering":
                    message = f"No {sector_name}, seu uso de volante difere da referência."
                elif main_metric == "gear":
                    message = f"No {sector_name}, sua seleção de marcha difere da referência."
                else:
                    message = f"No {sector_name}, há diferenças em {main_metric}."

                sector_insights.append({
                    "sector": sector_name,
                    "message": message,
                    "main_metric": main_metric,
                    "severity": severity,
                    "evidence": {
                        "mean_diff": mean_diff,
                        "mean_abs_diff": max_diff
                    }
                })

    return {
        "summary": summary,
        "priority": priority,
        "recommendations": recommendations,
        "sector_insights": sector_insights
    }
