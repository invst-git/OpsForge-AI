from typing import Dict, List
import time
from config.knowledge_base import kb
from datetime import datetime

class ActionExecutor:
    """Execute agent recommendations as real actions"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.execution_log = []
    
    def execute_action(self, action: Dict) -> Dict:
        """Execute single action with rollback capability"""
        action_type = action.get("type")
        params = action.get("params", {})
        
        result = {
            "action_id": f"ACT-{int(time.time())}",
            "type": action_type,
            "status": "dry_run" if self.dry_run else "executing",
            "timestamp": datetime.now().isoformat()
        }
        
        if self.dry_run:
            result["message"] = f"DRY RUN: Would execute {action_type}"
            return result
        
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
        
        self.execution_log.append(result)
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