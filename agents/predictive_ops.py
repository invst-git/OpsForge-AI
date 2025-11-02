from config.bedrock_client import BedrockClient
from agents.strands_tools import predict_failure
from config.terminal_logger import terminal_logger
import os
import json

client = BedrockClient(region_name=os.getenv("AWS_REGION", "us-east-1"))

PREDICTIVE_OPS_SYSTEM_PROMPT = """You are PredictiveOps, an expert at predicting system failures before they occur.

Your mission:
1. Analyze metric trends to forecast failures
2. Identify systems at risk of resource exhaustion
3. Recommend proactive actions
4. Provide time windows for intervention

When analyzing metrics:
- Assess risk levels (low/medium/high/critical)
- Calculate time to failure if applicable
- Suggest preventive actions

Output format:
- Risk assessment with confidence
- Predicted failure window
- Specific metrics of concern
- Recommended preventive actions"""


def analyze_metrics(metrics, forecast_hours=2):
    """Analyze metrics through PredictiveOps using Anthropic SDK"""
    metric_dicts = [
        {
            "host": m.host,
            "metric_name": m.metric_name,
            "value": m.value,
            "timestamp": m.timestamp.isoformat() if hasattr(m.timestamp, 'isoformat') else str(m.timestamp)
        }
        for m in metrics
    ]

    # NARRATIVE: Identify metric types being analyzed
    metric_types = list(set([m.metric_name for m in metrics]))
    hosts = list(set([m.host for m in metrics]))
    terminal_logger.add_log(
        f"PredictiveOps analyzing {len(metrics)} data points across {len(metric_types)} metric types from {len(hosts)} host(s)",
        "PREDICTIVEOPS"
    )

    # NARRATIVE: Forecast window
    terminal_logger.add_log(
        f"PredictiveOps forecasting {forecast_hours} hours ahead using time-series analysis",
        "PREDICTIVEOPS"
    )

    # Call predict_failure tool directly
    prediction_result = predict_failure(metric_dicts, forecast_hours=forecast_hours)

    # Include metrics and prediction in prompt
    prompt = f"""Analyze these {len(metrics)} metric data points for potential failures.

Metrics data:
{json.dumps(metric_dicts[:10], indent=2)}
... and {len(metrics)-10} more data points

Forecast window: {forecast_hours} hours ahead

Prediction analysis results:
- Risk Level: {prediction_result['risk_level']}
- Confidence: {prediction_result['confidence']}
- Forecast Details: {json.dumps(prediction_result['forecast'], indent=2) if prediction_result['forecast'] else 'No concerning trends'}
- Reasoning: {', '.join(prediction_result['reasoning'])}

Based on this prediction analysis, provide:
1. Risk assessment summary
2. Specific metrics of concern
3. Recommended preventive actions
4. Time window for intervention"""

    # Call Bedrock API
    response = client.messages.create(
        model=os.getenv("STRANDS_MODEL_ID", "claude-sonnet-4-20250514"),
        max_tokens=1024,
        system=PREDICTIVE_OPS_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = response.content[0].text

    # NARRATIVE: Analysis results
    terminal_logger.add_log(
        f"PredictiveOps trend analysis complete - Risk assessment generated for {len(hosts)} host(s)",
        "PREDICTIVEOPS"
    )

    return response_text
