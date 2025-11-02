from config.bedrock_client import BedrockClient
from agents.strands_tools import correlate_alerts
from config.knowledge_base import kb
from config.terminal_logger import terminal_logger
import os
import json

client = BedrockClient(region_name=os.getenv("AWS_REGION", "us-east-1"))

ALERT_OPS_SYSTEM_PROMPT = """You are AlertOps, an expert alert correlation agent with memory.

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

Always provide confidence scores and reference past learnings when applicable.

When you need to correlate alerts, call the correlate_alerts function with the alert data."""


def analyze_alert_stream_with_memory(alerts):
    """Process alerts with historical context using AWS Bedrock"""
    alert_list = [
        {
            "alert_id": a.alert_id,
            "title": a.title,
            "host": a.host,
            "timestamp": a.timestamp.isoformat() if hasattr(a.timestamp, 'isoformat') else str(a.timestamp),
            "severity": a.severity.value
        }
        for a in alerts
    ]

    # NARRATIVE: Check historical context
    keywords = list(set([a.title.split()[0] for a in alerts]))
    terminal_logger.add_log(
        f"AlertOps checking knowledge base for similar past incidents (keywords: {', '.join(keywords[:3])})",
        "ALERTOPS"
    )

    similar = kb.get_similar_incidents(keywords, limit=3)

    context = ""
    if similar:
        context = f"\nPast similar incidents: {len(similar)} found. "
        context += f"Example root cause: {similar[0].get('root_cause', 'N/A')}"

        # NARRATIVE: Found similar incidents
        terminal_logger.add_log(
            f"AlertOps found {len(similar)} similar past incidents for pattern matching",
            "ALERTOPS"
        )
    else:
        terminal_logger.add_log(
            "AlertOps found no similar past incidents - analyzing as new pattern",
            "ALERTOPS"
        )

    # NARRATIVE: Running correlation algorithm
    terminal_logger.add_log(
        f"AlertOps running graph-based correlation algorithm on {len(alerts)} alerts",
        "ALERTOPS"
    )

    # Call correlate_alerts tool directly
    correlation_result = correlate_alerts(alert_list)

    # Build prompt with correlation data
    prompt = f"""Analyze these {len(alerts)} alerts:{context}

{chr(10).join([f"- [{a['severity']}] {a['title']} on {a['host']}" for a in alert_list])}

Correlation analysis results:
- Primary Alert: {correlation_result['primary_alert_id']}
- Related Alerts: {len(correlation_result['related_alert_ids'])} alerts
- Confidence: {correlation_result['confidence']}
- Root Cause: {correlation_result['root_cause']}
- Reasoning: {', '.join(correlation_result['reasoning'])}

Based on this correlation analysis and your memory, provide:
1. Incident summary
2. Recommended actions
3. Confidence level"""

    # Call Bedrock API
    response = client.messages.create(
        model=os.getenv("STRANDS_MODEL_ID", "claude-sonnet-4-20250514"),
        max_tokens=1024,
        system=ALERT_OPS_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = response.content[0].text

    # NARRATIVE: Analysis complete with results
    hosts = list(set([a.host for a in alerts]))
    terminal_logger.add_log(
        f"AlertOps correlation complete - Analyzed alerts from {len(hosts)} host(s): {', '.join(hosts[:3])}",
        "ALERTOPS"
    )

    # Store learning
    kb.store_agent_knowledge(
        "AlertOps",
        f"correlation_{alerts[0].alert_id}",
        {"alerts": [a.alert_id for a in alerts], "analysis": response_text[:200]}
    )

    # NARRATIVE: Storing learning
    terminal_logger.add_log(
        "AlertOps storing correlation pattern in knowledge base for future reference",
        "LEARNING"
    )

    return response_text
