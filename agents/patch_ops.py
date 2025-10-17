from strands import Agent
from tools.patch_ops import (
    run_preflight_checks, 
    deploy_canary, 
    verify_health, 
    rollback_patch,
    deploy_full_patch
)
from config.knowledge_base import kb
import os

patch_ops_agent = Agent(
    name="PatchOps",
    model=os.getenv("STRANDS_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0"),
    tools=[run_preflight_checks, deploy_canary, verify_health, rollback_patch, deploy_full_patch],
    system_prompt="""You are PatchOps, the safe patching specialist with autonomous deployment capabilities.

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
)

def safe_patch_deployment(host: str, patch_id: str):
    """Execute safe patch deployment with canary"""
    
    # Check past patterns
    patterns = kb.get_patterns_by_type('patch_deployment')
    context = ""
    if patterns:
        context = f"\n\nHistorical data: {len(patterns)} past deployments found."
    
    prompt = f"""Execute safe patch deployment for {patch_id} on {host}.{context}

Follow the canary deployment workflow:
1. Pre-flight checks
2. Canary deployment (25%)
3. Health verification
4. Decision: rollback or proceed
5. Full deployment if safe

Use your tools autonomously and provide detailed status at each step."""
    
    response = patch_ops_agent(prompt)
    
    # Store outcome
    kb.store_pattern('patch_deployment', {
        'patch_id': patch_id,
        'host': host,
        'confidence': 0.85,
        'details': {'response': str(response)[:200]}
    })
    
    return response