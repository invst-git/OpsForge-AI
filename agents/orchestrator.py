from strands import Agent
from config.perception import AgentPerception
from config.learning import AgentLearning
from config.knowledge_base import kb
import os
import uuid

orchestrator_agent = Agent(
    name="Orchestrator",
    model=os.getenv("STRANDS_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0"),
    system_prompt="""You are the Orchestrator with perception, memory, and learning.

ENHANCED CAPABILITIES:
- Perceive environment with context awareness
- Access historical knowledge and patterns
- Learn from outcomes to improve decisions
- Coordinate 5 specialist agents

Agents:
- AlertOps: Correlation
- PredictiveOps: Forecasting
- PatchOps: Safe patching
- TaskOps: Automation
- Orchestrator: You

Always reference learned patterns and adjust confidence based on past outcomes."""
)

class EnhancedOrchestrator:
    def __init__(self):
        self.perception = AgentPerception("Orchestrator")
        self.learning = AgentLearning()
        self.audit_log = []
    
    def handle_incident_full(self, alerts, metrics=None, incident_id=None):
        """Full pipeline: Perceive → Reason → Act → Learn"""

        # PERCEPTION
        alert_perception = self.perception.perceive_alerts([
            {"alert_id": a.alert_id, "title": a.title, "host": a.host,
             "timestamp": a.timestamp, "severity": a.severity.value}
            for a in alerts
        ])

        metric_perception = None
        if metrics:
            metric_perception = self.perception.perceive_metrics([
                {"host": m.host, "metric_name": m.metric_name,
                 "value": m.value, "timestamp": m.timestamp}
                for m in metrics
            ])

        # KNOWLEDGE
        learned = self.learning.get_learned_patterns("Orchestrator", "correlation")

        # REASONING (delegate to specialist agents)
        from agents.alert_ops import analyze_alert_stream_with_memory
        from agents.predictive_ops import analyze_metrics

        alert_analysis = analyze_alert_stream_with_memory(alerts)
        prediction = analyze_metrics(metrics) if metrics else None

        # SYNTHESIS
        synthesis = self._synthesize(alert_analysis, prediction, learned)

        # ACTION (store or update incident)
        if not incident_id:
            # Create new incident if not provided
            incident_id = kb.store_incident({
                "incident_id": f"INC-{uuid.uuid4().hex[:8]}",
                "alerts": [a.alert_id for a in alerts],
                "root_cause": str(synthesis)[:100],
                "agents_involved": ["AlertOps", "PredictiveOps", "Orchestrator"],
                "outcome": "pending"
            })
        else:
            # Update the existing placeholder incident with real results
            existing_incident = kb.get_incident(incident_id)
            if existing_incident:
                print(f"🔄 Updating incident {incident_id} with real results")
                existing_incident.update({
                    "root_cause": str(synthesis)[:200],
                    "agents_involved": ["AlertOps", "PredictiveOps", "Orchestrator"],
                    "outcome": "pending",
                    "metadata": {"status": "completed", "perception": str(alert_perception)[:500]}
                })
                kb.incident_memory[incident_id] = existing_incident
                print(f"✅ Updated incident {incident_id} successfully")
            else:
                print(f"⚠️ Warning: Could not find incident {incident_id} to update!")

        # MEMORY
        self._log_decision(incident_id, synthesis)

        return {
            "incident_id": incident_id,
            "perception": alert_perception,
            "learned_patterns": learned["successful_patterns"],
            "synthesis": synthesis
        }
    
    def _synthesize(self, alert_analysis, prediction, learned):
        context = f"""
Alert Analysis: {str(alert_analysis)[:300]}
Prediction: {str(prediction)[:200] if prediction else 'N/A'}
Learned Patterns: {learned['successful_patterns']} successful patterns in KB
"""
        prompt = f"Synthesize unified response:\n{context}"
        return orchestrator_agent(prompt)
    
    def _log_decision(self, incident_id, synthesis):
        self.audit_log.append({
            "incident_id": incident_id,
            "decision": str(synthesis)[:150]
        })

# Global instance
enhanced_orchestrator = EnhancedOrchestrator()