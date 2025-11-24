"""
Lightweight ETS-style (exponential smoothing with trend) forecaster for PredictiveOps.
Uses a simple Holt linear trend model to avoid external heavy dependencies while
still providing short-horizon forecasts and residual-based anomaly scores.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Sequence, Tuple


@dataclass
class HoltLinearResult:
    level: float
    trend: float
    fitted: List[float]
    forecast: List[float]
    residuals: List[float]


def holt_linear_forecast(
    values: Sequence[float],
    horizon: int = 12,
    alpha: float = 0.4,
    beta: float = 0.2,
) -> HoltLinearResult:
    """
    Simple Holt's linear trend (ETS without seasonality).

    Args:
        values: Ordered numeric series.
        horizon: Number of future points to forecast.
        alpha: Smoothing for level (0-1).
        beta: Smoothing for trend (0-1).
    """
    if len(values) == 0:
        return HoltLinearResult(0.0, 0.0, [], [0.0] * horizon, [])
    if len(values) == 1:
        single = float(values[0])
        return HoltLinearResult(single, 0.0, [single], [single] * horizon, [0.0])

    level = float(values[0])
    trend = float(values[1] - values[0])
    fitted: List[float] = []
    residuals: List[float] = []

    for i, actual in enumerate(values):
        if i == 0:
            fitted.append(level)
            residuals.append(actual - level)
            continue

        last_level = level
        level = alpha * actual + (1 - alpha) * (level + trend)
        trend = beta * (level - last_level) + (1 - beta) * trend

        prediction = level + trend
        fitted.append(prediction)
        residuals.append(actual - prediction)

    forecast = [level + (k + 1) * trend for k in range(horizon)]

    return HoltLinearResult(level, trend, fitted, forecast, residuals)


def _z_score(latest_residual: float, residuals: Sequence[float]) -> float:
    """Compute a simple z-score against residuals, guarding against zero std."""
    if not residuals:
        return 0.0
    mean = sum(residuals) / len(residuals)
    variance = sum((r - mean) ** 2 for r in residuals) / max(len(residuals), 1)
    std = variance ** 0.5
    if std == 0:
        return 0.0
    return abs(latest_residual - mean) / std


def generate_ets_summary(metric_points: List[Dict], horizon: int = 12, min_points: int = 5) -> Dict:
    """
    Build ETS forecasts per (host, metric) pair from raw metric dicts.

    metric_points items must include: host, metric_name, value, timestamp.
    """
    # Group by host/metric
    grouped: Dict[Tuple[str, str], List[Tuple[datetime, float]]] = {}
    for m in metric_points:
        host = m.get("host", "unknown")
        name = m.get("metric_name", "metric")
        value = float(m.get("value", 0.0))
        ts = m.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                ts = datetime.now()
        elif not isinstance(ts, datetime):
            ts = datetime.now()

        key = (host, name)
        grouped.setdefault(key, []).append((ts, value))

    series_summaries = []
    anomalies = []

    for (host, name), points in grouped.items():
        points.sort(key=lambda p: p[0])
        values = [p[1] for p in points]
        if len(values) < min_points:
            continue

        result = holt_linear_forecast(values, horizon=horizon)
        last_value = values[-1]
        latest_residual = result.residuals[-1] if result.residuals else 0.0
        z = _z_score(latest_residual, result.residuals)

        series_summary = {
            "host": host,
            "metric": name,
            "last_value": round(last_value, 2),
            "trend": round(result.trend, 4),
            "forecast": [round(v, 2) for v in result.forecast[: min(horizon, 8)]],
            "anomaly_score": round(z, 3),
        }
        series_summaries.append(series_summary)

        anomalies.append({
            "host": host,
            "metric": name,
            "z_score": round(z, 3),
            "residual": round(latest_residual, 3),
            "trend": round(result.trend, 4),
        })

    anomalies.sort(key=lambda a: a["z_score"], reverse=True)

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "horizon": horizon,
        "series": series_summaries,
        "top_anomalies": anomalies[:5],
    }
