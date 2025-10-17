from strands import Agent
from tools.task_ops import (
    execute_vpn_reset,
    verify_backup,
    audit_licenses,
    clear_disk_space,
    restart_service
)
from config.knowledge_base import kb
import os

task_ops_agent = Agent(
    name="TaskOps",
    model=os.getenv("STRANDS_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0"),
    tools=[execute_vpn_reset, verify_backup, audit_licenses, clear_disk_space, restart_service],
    system_prompt="""You are TaskOps, automating routine IT tasks.

CAPABILITIES:
- VPN resets
- Backup verification
- License audits
- Disk cleanup
- Service restarts

WORKFLOW:
1. Understand task request
2. Execute with appropriate tool
3. Verify completion
4. Report results

SAFETY:
- Dry-run for HIGH risk tasks
- Auto-execute LOW risk tasks
- Log all actions

Save ~8 hours/engineer/week by automating routine work."""
)

def automate_task(task_type: str, params: dict):
    """Execute automated task"""
    
    prompt = f"""Execute this task: {task_type}
Parameters: {params}

Use the appropriate tool and report completion status."""
    
    response = task_ops_agent(prompt)
    
    # Store execution
    kb.store_agent_knowledge("TaskOps", f"task_{task_type}", {
        "params": params,
        "result": str(response)[:150]
    })
    
    return response