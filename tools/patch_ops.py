from strands.tools import tool
from typing import Dict, List
import time
import random

@tool
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
        "disk_space": random.choice([True, True, True, False]),  # 75% pass
        "backup_verified": True,
        "service_health": random.choice([True, True, False]),  # 66% pass
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

@tool
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
    time.sleep(0.5)  # Simulate deployment
    
    success = random.random() > 0.2  # 80% success rate
    
    return {
        "host": host,
        "patch_id": patch_id,
        "canary_percentage": canary_percentage,
        "status": "success" if success else "failed",
        "canary_hosts": [f"{host}-canary-{i}" for i in range(1, 4)],
        "deployment_time": "30s"
    }

@tool
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

@tool
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

@tool
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