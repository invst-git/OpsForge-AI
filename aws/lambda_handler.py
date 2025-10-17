import json
import boto3
from agents.orchestrator import orchestrator
from data.models import Alert, Metric, Severity, AlertStatus
from datetime import datetime

def lambda_handler(event, context):
    """AWS Lambda entry point for OpsForge AI"""
    
    try:
        # Parse event
        event_type = event.get('type')
        
        if event_type == 'alerts':
            return handle_alerts(event.get('data', []))
        elif event_type == 'metrics':
            return handle_metrics(event.get('data', []))
        elif event_type == 'incident':
            return handle_incident(event.get('alerts', []), event.get('metrics', []))
        else:
            return error_response(f"Unknown event type: {event_type}")
    
    except Exception as e:
        return error_response(str(e))

def handle_alerts(alert_data):
    """Process alert-only events"""
    alerts = parse_alerts(alert_data)
    result = orchestrator.handle_incident(alerts, metrics=None)
    
    return success_response({
        'incident_type': 'alert_correlation',
        'analysis': str(result)[:1000]  # Truncate for Lambda limits
    })

def handle_metrics(metric_data):
    """Process metric-only events"""
    metrics = parse_metrics(metric_data)
    
    from agents.predictive_ops import analyze_metrics
    result = analyze_metrics(metrics)
    
    return success_response({
        'incident_type': 'prediction',
        'analysis': str(result)[:1000]
    })

def handle_incident(alert_data, metric_data):
    """Process full incident with alerts + metrics"""
    alerts = parse_alerts(alert_data)
    metrics = parse_metrics(metric_data) if metric_data else None
    
    result = orchestrator.handle_incident(alerts, metrics)
    
    return success_response({
        'incident_type': 'full_response',
        'analysis': str(result)[:1000]
    })

def parse_alerts(data):
    """Parse alert JSON to Alert objects"""
    return [
        Alert(
            alert_id=a.get('alert_id'),
            title=a.get('title'),
            description=a.get('description', ''),
            severity=Severity(a.get('severity', 'medium')),
            source=a.get('source', 'unknown'),
            host=a.get('host'),
            timestamp=datetime.fromisoformat(a.get('timestamp')),
            status=AlertStatus(a.get('status', 'open')),
            tags=a.get('tags', []),
            metadata=a.get('metadata', {})
        )
        for a in data
    ]

def parse_metrics(data):
    """Parse metric JSON to Metric objects"""
    return [
        Metric(
            metric_id=m.get('metric_id'),
            host=m.get('host'),
            metric_name=m.get('metric_name'),
            value=float(m.get('value')),
            timestamp=datetime.fromisoformat(m.get('timestamp')),
            unit=m.get('unit', 'percent')
        )
        for m in data
    ]

def success_response(data):
    return {
        'statusCode': 200,
        'body': json.dumps(data),
        'headers': {'Content-Type': 'application/json'}
    }

def error_response(error):
    return {
        'statusCode': 500,
        'body': json.dumps({'error': error}),
        'headers': {'Content-Type': 'application/json'}
    }
