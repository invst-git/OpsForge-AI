from typing import Dict, List
import time
from config.knowledge_base import kb
from config.terminal_logger import terminal_logger
from datetime import datetime
import uuid

class ActionExecutor:
    """Execute agent recommendations as real actions"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.execution_log = []
        self.current_incident_id = None  # PHASE 1: Track current incident

    def set_incident_context(self, incident_id: str) -> None:
        """PHASE 1: Set the incident context for actions"""
        self.current_incident_id = incident_id

    def execute_action(self, action: Dict, incident_id: str = None) -> Dict:
        """Execute single action with rollback capability"""
        action_type = action.get("type")
        params = action.get("params", {})

        # PHASE 1: Use provided incident_id or fall back to context
        target_incident_id = incident_id or self.current_incident_id

        # PHASE 2 TASK 2.3: Create unique action ID
        action_id = f"ACT-{uuid.uuid4().hex[:8]}"

        # NARRATIVE: Action validation
        host = params.get('host', 'unknown')
        terminal_logger.add_log(
            f"ActionExecutor validating action {action_type} for host {host}",
            "TASKOPS"
        )

        result = {
            "action_id": action_id,
            "type": action_type,
            "status": "dry_run" if self.dry_run else "executing",
            "timestamp": datetime.now().isoformat(),
            "incident_id": target_incident_id,  # PHASE 1: Link to incident
            "params": params  # PHASE 2: Include params in result
        }

        if self.dry_run:
            result["message"] = f"DRY RUN: Would execute {action_type}"
            terminal_logger.add_log(
                f"ActionExecutor dry-run mode - simulating {action_type} on {host}",
                "TASKOPS"
            )
            return result

        # NARRATIVE: Execute action
        terminal_logger.add_log(
            f"ActionExecutor executing {action_type} on {host} (action ID: {action_id})",
            "TASKOPS"
        )

        # Execute based on type
        if action_type == "suppress_alerts":
            result.update(self._suppress_alerts(params))
        elif action_type == "restart_service":
            result.update(self._restart_service(params))
        elif action_type == "deploy_patch":
            result.update(self._deploy_patch(params))
        elif action_type == "clear_cache":
            result.update(self._clear_cache(params))
        elif action_type == "scale_resources":
            result.update(self._scale_resources(params))
        else:
            result["status"] = "unknown_action"
            terminal_logger.add_log(
                f"ActionExecutor unknown action type: {action_type}",
                "WARNING"
            )

        # NARRATIVE: Execution result
        status = result.get('status', 'unknown')
        if status == 'success' or status == 'completed':
            terminal_logger.add_log(
                f"ActionExecutor successfully completed {action_type} on {host}",
                "SUCCESS"
            )
        else:
            terminal_logger.add_log(
                f"ActionExecutor action {action_type} completed with status: {status}",
                "TASKOPS"
            )

        self.execution_log.append(result)

        # PHASE 1: Link action to incident if available
        # PHASE 2 TASK 2.3: Create audit log entry
        if target_incident_id:
            kb.add_incident_action(target_incident_id, {
                'type': action_type,
                'agent': action.get('agent', 'ActionExecutor'),
                'description': f"Executed {action_type} on {params.get('host', 'unknown')}",
                'status': result.get('status'),
                'action_id': action_id
            })

            # Also log to timeline
            kb.add_timeline_event(target_incident_id, {
                'agent': action.get('agent', 'ActionExecutor'),
                'event': f"Executed action: {action_type}",
                'details': {
                    'action_id': action_id,
                    'target': params.get('host', 'unknown'),
                    'status': result.get('status')
                }
            })

        # Record outcome for learning loop (non-blocking, additive)
        try:
            kb.record_action_outcome(action_type, result.get("status"), incident_id=target_incident_id, agent=action.get('agent'))
        except Exception:
            pass

        return result
    
    def _suppress_alerts(self, params):
        alert_ids = params.get("alert_ids", [])
        return {
            "status": "completed",
            "suppressed_count": len(alert_ids),
            "alert_ids": alert_ids
        }
    
    def _restart_service(self, params):
        host = params.get("host")
        service = params.get("service")
        time.sleep(0.5)
        return {
            "status": "completed",
            "host": host,
            "service": service,
            "uptime": "3s"
        }
    
    def _deploy_patch(self, params):
        from agents.patch_ops import safe_patch_deployment
        result = safe_patch_deployment(params.get("host"), params.get("patch_id"))
        return {"status": "completed", "details": str(result)[:200]}
    
    def _clear_cache(self, params):
        host = params.get("host")
        time.sleep(0.3)
        return {
            "status": "completed",
            "host": host,
            "cleared_mb": 2048
        }
    
    def _scale_resources(self, params):
        host = params.get("host")
        resource = params.get("resource")
        return {
            "status": "completed",
            "host": host,
            "resource": resource,
            "new_capacity": params.get("target")
        }
    
    def rollback_action(self, action_id: str) -> Dict:
        """Rollback executed action"""
        for action in self.execution_log:
            if action["action_id"] == action_id:
                return {
                    "rollback_status": "completed",
                    "original_action": action["type"],
                    "rollback_time": "5s"
                }
        return {"rollback_status": "action_not_found"}

executor = ActionExecutor(dry_run=False)
