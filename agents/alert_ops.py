from strands import Agent
from tools.correlation import correlate_alerts
from config.knowledge_base import kb
import os

alert_ops_agent = Agent(
    name="AlertOps",
    model=os.getenv("STRANDS_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0"),
    tools=[correlate_alerts],
    system_prompt="""You are AlertOps, an expert alert correlation agent with memory.

MEMORY ACCESS:
You can learn from past incidents. Before analyzing new alerts, consider:
- Similar past incidents and their root causes
- Patterns that worked before
- Correlation confidence from history

Your mission:
1. Check knowledge base for similar incidents
2. Analyze incoming alerts for correlation
3. Learn from outcomes to improve future decisions
4. Store successful patterns for reuse

Always provide confidence scores and reference past learnings when applicable."""
)

def analyze_alert_stream_with_memory(alerts):
    """Process alerts with historical context"""
    alert_list = [
        {
            "alert_id": a.alert_id,
            "title": a.title,
            "host": a.host,
            "timestamp": a.timestamp,
            "severity": a.severity.value
        }
        for a in alerts
    ]
    
    # Check for similar past incidents
    keywords = list(set([a.title.split()[0] for a in alerts]))
    similar = kb.get_similar_incidents(keywords, limit=3)
    
    context = ""
    if similar:
        context = f"\nPast similar incidents: {len(similar)} found. "
        context += f"Example root cause: {similar[0].get('root_cause', 'N/A')}"
    
    prompt = f"""Analyze these {len(alerts)} alerts:{context}

{chr(10).join([f"- [{a['severity']}] {a['title']} on {a['host']}" for a in alert_list])}

Use correlate_alerts tool and your memory to provide analysis."""
    
    response = alert_ops_agent(prompt)
    
    # Store learning
    kb.store_agent_knowledge(
        "AlertOps",
        f"correlation_{alerts[0].alert_id}",
        {"alerts": [a.alert_id for a in alerts], "analysis": str(response)[:200]}
    )
    
    return response