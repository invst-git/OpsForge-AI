from agents.orchestrator import enhanced_orchestrator
from config.action_executor import executor

def execute_incident_response(alerts, metrics=None, auto_execute=True):
    """Full incident response with action execution"""
    
    # Analyze
    result = enhanced_orchestrator.handle_incident_full(alerts, metrics)
    
    # Extract actions from synthesis
    actions = parse_actions_from_synthesis(str(result["synthesis"]))
    
    executed = []
    for action in actions:
        if auto_execute and action["risk_level"] in ["LOW", "MEDIUM"]:
            exec_result = executor.execute_action(action)
            executed.append(exec_result)
        else:
            executed.append({"status": "requires_approval", "action": action})
    
    return {
        "incident": result,
        "actions_executed": executed
    }

def parse_actions_from_synthesis(synthesis: str) -> list:
    """Parse recommended actions from agent output"""
    synthesis = synthesis.lower()
    actions = []
    
    if "suppress" in synthesis or "correlation" in synthesis:
        actions.append({
            "type": "suppress_alerts",
            "params": {"alert_ids": ["example"]},
            "risk_level": "LOW"
        })
    
    if "restart" in synthesis:
        actions.append({
            "type": "restart_service",
            "params": {"host": "web-01", "service": "nginx"},
            "risk_level": "MEDIUM"
        })
    
    return actions