from strands import Agent
from tools.prediction import predict_failure
import os
import json

predictive_ops_agent = Agent(
    name="PredictiveOps",
    model=os.getenv("STRANDS_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0"),
    tools=[predict_failure],
    system_prompt="""You are PredictiveOps, an expert at predicting system failures before they occur.

Your mission:
1. Analyze metric trends to forecast failures
2. Identify systems at risk of resource exhaustion
3. Recommend proactive actions
4. Provide time windows for intervention

When analyzing metrics:
- Use predict_failure tool with the provided metrics
- Assess risk levels (low/medium/high/critical)
- Calculate time to failure if applicable
- Suggest preventive actions

Output format:
- Risk assessment with confidence
- Predicted failure window
- Specific metrics of concern
- Recommended preventive actions"""
)

def analyze_metrics(metrics, forecast_hours=2):
    """Analyze metrics through PredictiveOps agent"""
    metric_dicts = [
        {
            "host": m.host,
            "metric_name": m.metric_name,
            "value": m.value,
            "timestamp": m.timestamp.isoformat()
        }
        for m in metrics
    ]
    
    # Include metrics in prompt
    prompt = f"""Analyze these {len(metrics)} metric data points for potential failures.

Metrics data:
{json.dumps(metric_dicts[:10], indent=2)}
... and {len(metrics)-10} more data points

Forecast window: {forecast_hours} hours ahead

Use the predict_failure tool with these metrics and provide your risk assessment."""
    
    return predictive_ops_agent(prompt)
