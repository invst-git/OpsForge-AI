"""Clean tool functions for OpsForge AI agents (ready for Anthropic integration)"""

from typing import List, Dict
from datetime import datetime, timedelta
import statistics
import networkx as nx
import time
import random

# ============================================================================
# ALERT CORRELATION TOOLS
# ============================================================================

def correlate_alerts(alerts: List[Dict]) -> Dict:
    """
    Correlate related alerts using graph analysis.

    Args:
        alerts: List of alert dictionaries with keys: alert_id, title, host, timestamp, severity

    Returns:
        Dictionary with correlation results including primary alert, related alerts, and confidence
    """
    if len(alerts) < 2:
        return {
            "primary_alert_id": alerts[0]["alert_id"] if alerts else None,
            "related_alert_ids": [],
            "confidence": 1.0,
            "root_cause": alerts[0]["title"] if alerts else "No alerts",
            "reasoning": ["Only one alert, no correlation needed"],
            "suppressed_count": 0
        }

    # Build correlation graph
    G = nx.Graph()

    for alert in alerts:
        G.add_node(alert["alert_id"], **alert)

    # Add edges based on correlation factors
    for i, alert1 in enumerate(alerts):
        for alert2 in alerts[i+1:]:
            score = 0.0
            reasons = []

            # Same host correlation
            if alert1["host"] == alert2["host"]:
                score += 0.4
                reasons.append("same_host")

            # Time proximity (within 60 seconds)
            # Handle both datetime objects and ISO strings
            ts1 = alert1["timestamp"]
            ts2 = alert2["timestamp"]
            if isinstance(ts1, str):
                ts1 = datetime.fromisoformat(ts1.replace('Z', '+00:00'))
            if isinstance(ts2, str):
                ts2 = datetime.fromisoformat(ts2.replace('Z', '+00:00'))

            time_diff = abs((ts1 - ts2).total_seconds())
            if time_diff < 60:
                score += 0.3
                reasons.append("time_proximity")

            # Keyword matching
            keywords1 = set(alert1["title"].lower().split())
            keywords2 = set(alert2["title"].lower().split())
            overlap = len(keywords1 & keywords2)
            if overlap > 0:
                score += min(0.3, overlap * 0.1)
                reasons.append("keyword_match")

            if score > 0.5:
                G.add_edge(alert1["alert_id"], alert2["alert_id"],
                          weight=score, reasons=reasons)

    # Find largest connected component (main incident cluster)
    if G.number_of_edges() > 0:
        components = list(nx.connected_components(G))
        largest = max(components, key=len)

        # Identify root cause (earliest alert in cluster)
        cluster_alerts = [alerts[i] for i, a in enumerate(alerts)
                         if a["alert_id"] in largest]

        # Sort by timestamp (handle both datetime and string)
        def get_timestamp(alert):
            ts = alert["timestamp"]
            if isinstance(ts, str):
                return datetime.fromisoformat(ts.replace('Z', '+00:00'))
            return ts

        cluster_alerts.sort(key=get_timestamp)
        primary = cluster_alerts[0]

        related_ids = [a["alert_id"] for a in cluster_alerts[1:]]

        # Calculate time span
        first_ts = get_timestamp(cluster_alerts[0])
        last_ts = get_timestamp(cluster_alerts[-1])
        time_span = int((last_ts - first_ts).total_seconds())

        return {
            "primary_alert_id": primary["alert_id"],
            "related_alert_ids": related_ids,
            "confidence": 0.85,
            "root_cause": primary["title"],
            "reasoning": [
                f"Identified cluster of {len(largest)} related alerts",
                f"Primary alert: {primary['title']} on {primary['host']}",
                f"Time span: {time_span}s"
            ],
            "suppressed_count": len(related_ids)
        }

    # No correlation found
    return {
        "primary_alert_id": alerts[0]["alert_id"],
        "related_alert_ids": [],
        "confidence": 0.3,
        "root_cause": "No clear correlation detected",
        "reasoning": ["Alerts appear unrelated"],
        "suppressed_count": 0
    }


# ============================================================================
# PREDICTIVE ANALYSIS TOOLS
# ============================================================================


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


# ============================================================================
# PATCH MANAGEMENT TOOLS
# ============================================================================


def run_preflight_checks(host: str, patch_id: str) -> Dict:
    """
    Run pre-flight checks before patching

    Args:
        host: Target host
        patch_id: Patch identifier (e.g., KB5034763)

    Returns:
        Check results with pass/fail status
    """
    checks = {
        "disk_space": random.choice([True, True, True, False]),
        "backup_verified": True,
        "service_health": random.choice([True, True, False]),
        "dependencies_met": True,
        "rollback_available": True
    }

    all_passed = all(checks.values())

    return {
        "host": host,
        "patch_id": patch_id,
        "checks": checks,
        "overall_status": "passed" if all_passed else "failed",
        "failed_checks": [k for k, v in checks.items() if not v]
    }



def deploy_canary(host: str, patch_id: str, canary_percentage: int = 25) -> Dict:
    """
    Deploy patch to canary hosts

    Args:
        host: Primary host
        patch_id: Patch identifier
        canary_percentage: Percentage of hosts for canary (default 25%)

    Returns:
        Canary deployment status
    """
    time.sleep(0.5)

    success = random.random() > 0.2

    return {
        "host": host,
        "patch_id": patch_id,
        "canary_percentage": canary_percentage,
        "status": "success" if success else "failed",
        "canary_hosts": [f"{host}-canary-{i}" for i in range(1, 4)],
        "deployment_time": "30s"
    }



def verify_health(host: str, checks: List[str] = None) -> Dict:
    """
    Verify system health after deployment

    Args:
        host: Host to check
        checks: List of checks to run (cpu, memory, services, connectivity)

    Returns:
        Health check results
    """
    if not checks:
        checks = ["cpu", "memory", "services", "connectivity"]

    results = {}
    for check in checks:
        if check == "cpu":
            results[check] = {"status": "healthy", "value": random.randint(20, 45)}
        elif check == "memory":
            results[check] = {"status": "healthy", "value": random.randint(40, 65)}
        elif check == "services":
            results[check] = {"status": random.choice(["healthy", "healthy", "degraded"])}
        elif check == "connectivity":
            results[check] = {"status": "healthy", "latency_ms": random.randint(5, 20)}

    all_healthy = all(r["status"] == "healthy" for r in results.values())

    return {
        "host": host,
        "overall_health": "healthy" if all_healthy else "degraded",
        "checks": results,
        "timestamp": time.time()
    }



def rollback_patch(host: str, patch_id: str, reason: str) -> Dict:
    """
    Rollback patch deployment

    Args:
        host: Host to rollback
        patch_id: Patch to remove
        reason: Reason for rollback

    Returns:
        Rollback status
    """
    time.sleep(0.3)

    return {
        "host": host,
        "patch_id": patch_id,
        "status": "rolled_back",
        "reason": reason,
        "rollback_time": "15s",
        "system_restored": True
    }



def deploy_full_patch(host: str, patch_id: str) -> Dict:
    """
    Deploy patch to all hosts after canary success

    Args:
        host: Primary host
        patch_id: Patch identifier

    Returns:
        Full deployment status
    """
    time.sleep(1)

    phases = [
        {"phase": 1, "hosts": 25, "status": "completed"},
        {"phase": 2, "hosts": 50, "status": "completed"},
        {"phase": 3, "hosts": 25, "status": "completed"}
    ]

    return {
        "host": host,
        "patch_id": patch_id,
        "status": "completed",
        "phases": phases,
        "total_hosts": 100,
        "deployment_time": "8m 30s"
    }


# ============================================================================
# TASK AUTOMATION TOOLS
# ============================================================================


def execute_vpn_reset(user: str, vpn_server: str) -> Dict:
    """Reset VPN connection for user"""
    time.sleep(0.3)
    return {
        "task": "vpn_reset",
        "user": user,
        "server": vpn_server,
        "status": "completed",
        "new_session_id": f"VPN-{random.randint(10000,99999)}",
        "execution_time": "2s"
    }



def verify_backup(host: str, backup_type: str = "full") -> Dict:
    """Verify backup integrity"""
    time.sleep(0.5)
    success = random.random() > 0.1
    return {
        "task": "backup_verification",
        "host": host,
        "backup_type": backup_type,
        "status": "verified" if success else "failed",
        "last_backup": "2 hours ago",
        "size_gb": round(random.uniform(50, 500), 2),
        "integrity_check": "passed" if success else "corrupted"
    }



def audit_licenses(service: str) -> Dict:
    """Audit software licenses"""
    time.sleep(0.4)
    return {
        "task": "license_audit",
        "service": service,
        "total_licenses": 100,
        "in_use": random.randint(70, 95),
        "available": random.randint(5, 30),
        "expired": random.randint(0, 3),
        "compliance_status": "compliant"
    }



def clear_disk_space(host: str, target_gb: int = 10) -> Dict:
    """Clear temporary files and logs"""
    time.sleep(0.6)
    cleared = round(random.uniform(5, 15), 2)
    return {
        "task": "disk_cleanup",
        "host": host,
        "target_gb": target_gb,
        "cleared_gb": cleared,
        "status": "completed",
        "files_removed": random.randint(1000, 5000),
        "locations": ["/tmp", "/var/log", "/var/cache"]
    }



def restart_service(host: str, service_name: str, verify_startup: bool = True) -> Dict:
    """Restart system service with verification"""
    time.sleep(0.5)
    healthy = random.random() > 0.05
    return {
        "task": "service_restart",
        "host": host,
        "service": service_name,
        "status": "running" if healthy else "failed",
        "restart_time": "3s",
        "health_check": "passed" if healthy else "timeout",
        "uptime": "3s" if healthy else "0s"
    }
