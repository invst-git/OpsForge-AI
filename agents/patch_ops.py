from config.bedrock_client import BedrockClient
from agents.strands_tools import (
    run_preflight_checks,
    deploy_canary,
    verify_health,
    rollback_patch,
    deploy_full_patch
)
from config.knowledge_base import kb
from config.terminal_logger import terminal_logger
import os
import json

client = BedrockClient(region_name=os.getenv("AWS_REGION", "us-east-1"))

PATCH_OPS_SYSTEM_PROMPT = """You are PatchOps, the safe patching specialist with autonomous deployment capabilities.

PATCHING WORKFLOW:
1. Run pre-flight checks (disk, backup, services)
2. Deploy to canary hosts (25% of fleet)
3. Verify health for 5 minutes
4. If healthy: deploy to remaining hosts in phases
5. If unhealthy: immediate rollback

SAFETY RULES:
- Never skip pre-flight checks
- Always start with canary deployment
- Rollback if ANY health check fails
- Document every action with reasoning
- Auto-approve LOW risk, escalate HIGH risk

MEMORY:
Learn from past patch outcomes. Check knowledge base for:
- Past failures of same patch
- Success rates per patch type
- Common rollback triggers

Provide detailed execution plans with timelines."""


def safe_patch_deployment(host: str, patch_id: str):
    """Execute safe patch deployment with canary using Anthropic SDK"""

    # NARRATIVE: Starting patch evaluation
    terminal_logger.add_log(
        f"PatchOps evaluating patch {patch_id} for deployment to {host}",
        "PATCHOPS"
    )

    # Check past patterns
    patterns = kb.get_patterns_by_type('patch_deployment')
    context = ""
    if patterns:
        context = f"\n\nHistorical data: {len(patterns)} past deployments found."

        # NARRATIVE: Found historical data
        terminal_logger.add_log(
            f"PatchOps found {len(patterns)} past deployment patterns for risk assessment",
            "PATCHOPS"
        )
    else:
        terminal_logger.add_log(
            "PatchOps found no past deployment data - proceeding with standard safety protocol",
            "PATCHOPS"
        )

    # NARRATIVE: Deployment strategy
    terminal_logger.add_log(
        "PatchOps initiating canary deployment workflow (preflight -> canary -> verify -> full)",
        "PATCHOPS"
    )

    # Execute patch deployment workflow
    preflight = run_preflight_checks(host, patch_id)
    canary_result = None
    health_result = None
    final_deployment = None

    if preflight['overall_status'] == 'passed':
        canary_result = deploy_canary(host, patch_id, canary_percentage=25)
        if canary_result['status'] == 'success':
            health_result = verify_health(host, checks=["cpu", "memory", "services", "connectivity"])
            if health_result['overall_health'] == 'healthy':
                final_deployment = deploy_full_patch(host, patch_id)
            else:
                rollback_result = rollback_patch(host, patch_id, "Health check failed after canary")
                final_deployment = rollback_result

    # Build comprehensive prompt with all execution results
    prompt = f"""Execute safe patch deployment for {patch_id} on {host}.{context}

Canary deployment workflow execution results:

1. Pre-flight checks: {preflight['overall_status']}
   - Checks: {json.dumps(preflight['checks'], indent=2)}
   - Failed checks: {preflight['failed_checks']}

2. Canary deployment: {canary_result['status'] if canary_result else 'Skipped due to preflight failure'}
   {f"- Canary hosts: {canary_result['canary_hosts']}" if canary_result else ''}

3. Health verification: {health_result['overall_health'] if health_result else 'Skipped'}
   {f"- Health checks: {json.dumps(health_result['checks'], indent=2)}" if health_result else ''}

4. Final deployment: {final_deployment['status'] if final_deployment else 'Pending'}
   {f"- Total hosts: {final_deployment.get('total_hosts', 'N/A')}" if final_deployment and 'total_hosts' in final_deployment else ''}

Based on this execution, provide:
1. Deployment outcome summary
2. Risk assessment
3. Lessons learned for future deployments"""

    # Call Bedrock API
    response = client.messages.create(
        model=os.getenv("STRANDS_MODEL_ID", "claude-sonnet-4-20250514"),
        max_tokens=1024,
        system=PATCH_OPS_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = response.content[0].text

    # NARRATIVE: Deployment decision
    terminal_logger.add_log(
        f"PatchOps patch deployment workflow completed for {patch_id}",
        "PATCHOPS"
    )

    # Store outcome
    kb.store_pattern('patch_deployment', {
        'patch_id': patch_id,
        'host': host,
        'confidence': 0.85,
        'details': {'response': response_text[:200]}
    })

    # NARRATIVE: Store learning
    terminal_logger.add_log(
        "PatchOps storing deployment outcome in knowledge base for future risk assessment",
        "LEARNING"
    )

    return response_text
