from config.bedrock_client import BedrockClient
from agents.strands_tools import (
    execute_vpn_reset,
    verify_backup,
    audit_licenses,
    clear_disk_space,
    restart_service
)
from config.knowledge_base import kb
from config.terminal_logger import terminal_logger
import os
import json

client = BedrockClient(region_name=os.getenv("AWS_REGION", "us-east-1"))

TASK_OPS_SYSTEM_PROMPT = """You are TaskOps, automating routine IT tasks.

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


def automate_task(task_type: str, params: dict):
    """Execute automated task using Anthropic SDK"""

    # NARRATIVE: Task evaluation
    terminal_logger.add_log(
        f"TaskOps evaluating remediation task: {task_type}",
        "TASKOPS"
    )

    # Extract host if available
    host = params.get('host', 'unknown')
    terminal_logger.add_log(
        f"TaskOps preparing to execute {task_type} on {host}",
        "TASKOPS"
    )

    # Execute the appropriate tool based on task type
    execution_result = None
    try:
        if task_type == 'vpn_reset':
            execution_result = execute_vpn_reset(params.get('user', 'unknown'), params.get('vpn_server', 'vpn-01'))
        elif task_type == 'verify_backup':
            execution_result = verify_backup(host, params.get('backup_type', 'full'))
        elif task_type == 'audit_licenses':
            execution_result = audit_licenses(params.get('service', 'unknown'))
        elif task_type == 'clear_disk_space':
            execution_result = clear_disk_space(host, params.get('target_gb', 10))
        elif task_type == 'restart_service':
            execution_result = restart_service(host, params.get('service_name', 'unknown'), verify_startup=True)
        else:
            execution_result = {"error": f"Unknown task type: {task_type}"}
    except Exception as e:
        execution_result = {"error": str(e)}

    prompt = f"""Execute this task: {task_type}
Parameters: {json.dumps(params, indent=2)}

Execution results:
{json.dumps(execution_result, indent=2)}

Based on the execution results, provide:
1. Task completion status
2. Any issues encountered
3. Recommendations for optimization"""

    # Call Bedrock API
    response = client.messages.create(
        model=os.getenv("STRANDS_MODEL_ID", "claude-sonnet-4-20250514"),
        max_tokens=1024,
        system=TASK_OPS_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = response.content[0].text

    # NARRATIVE: Task execution complete
    terminal_logger.add_log(
        f"TaskOps completed execution of {task_type} on {host}",
        "TASKOPS"
    )

    # Store execution
    kb.store_agent_knowledge("TaskOps", f"task_{task_type}", {
        "params": params,
        "result": response_text[:150]
    })

    # NARRATIVE: Store learning
    terminal_logger.add_log(
        f"TaskOps storing task execution results for {task_type} in knowledge base",
        "LEARNING"
    )

    return response_text
