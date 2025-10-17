from strands.tools import tool
from typing import List, Dict
from datetime import datetime, timedelta
import statistics

@tool
def predict_failure(metrics: List[Dict], forecast_hours: int = 2) -> Dict:
    """
    Predict potential failures based on metric trends.
    
    Args:
        metrics: List of metric dictionaries with keys: host, metric_name, value, timestamp
        forecast_hours: Hours to forecast ahead
    
    Returns:
        Dictionary with prediction results including risk level and forecast
    """
    if len(metrics) < 5:
        return {
            "risk_level": "unknown",
            "confidence": 0.0,
            "forecast": {},
            "reasoning": ["Insufficient data for prediction"]
        }
    
    # Group by metric type
    by_metric = {}
    for m in metrics:
        key = f"{m['host']}_{m['metric_name']}"
        if key not in by_metric:
            by_metric[key] = []
        by_metric[key].append(m)
    
    predictions = []
    
    for key, data in by_metric.items():
        data.sort(key=lambda x: x["timestamp"])
        values = [d["value"] for d in data]
        
        # Simple trend analysis
        if len(values) >= 3:
            recent_trend = values[-1] - values[-3]
            avg_value = statistics.mean(values)
            
            # Predict failure conditions
            if "cpu" in key and avg_value > 80:
                predictions.append({
                    "metric": key,
                    "current": values[-1],
                    "trend": "increasing" if recent_trend > 0 else "stable",
                    "risk": "high" if values[-1] > 90 else "medium"
                })
            
            elif "memory" in key and avg_value > 85:
                predictions.append({
                    "metric": key,
                    "current": values[-1],
                    "trend": "increasing" if recent_trend > 0 else "stable",
                    "risk": "high" if values[-1] > 92 else "medium"
                })
    
    if predictions:
        high_risk = any(p["risk"] == "high" for p in predictions)
        return {
            "risk_level": "high" if high_risk else "medium",
            "confidence": 0.75,
            "forecast": predictions,
            "reasoning": [
                f"Analyzed {len(metrics)} data points",
                f"Found {len(predictions)} concerning trends",
                "Resource exhaustion predicted within forecast window"
            ]
        }
    
    return {
        "risk_level": "low",
        "confidence": 0.8,
        "forecast": [],
        "reasoning": ["All metrics within normal ranges"]
    }