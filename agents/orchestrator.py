from config.bedrock_client import BedrockClient
from config.perception import AgentPerception
from config.learning import AgentLearning
from config.knowledge_base import kb
from config.terminal_logger import terminal_logger
from config.agent_selector import agent_selector
import os
import uuid

client = BedrockClient(region_name=os.getenv("AWS_REGION", "us-east-1"))

ORCHESTRATOR_SYSTEM_PROMPT = """You are the Orchestrator with perception, memory, and learning.

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


class EnhancedOrchestrator:
    def __init__(self):
        self.perception = AgentPerception("Orchestrator")
        self.learning = AgentLearning()
        self.audit_log = []

    def handle_incident_full(self, alerts, metrics=None, incident_id=None):
        """Full pipeline: Perceive → Reason → Act → Learn

        Args:
            alerts: List of alert objects
            metrics: Optional list of metric objects
            incident_id: Optional incident ID for linking
        """

        # PHASE B: Intelligent agent selection based on incident content
        # Convert alerts to dict format for selector
        alert_dicts = [
            {"alert_id": a.alert_id, "title": a.title, "description": getattr(a, 'description', ''),
             "host": a.host, "severity": a.severity.value}
            for a in alerts
        ]

        metric_dicts = None
        if metrics:
            metric_dicts = [
                {"host": m.host, "metric_name": m.metric_name, "value": m.value}
                for m in metrics
            ]

        # Let AgentSelector intelligently choose relevant agents
        agents_involved = agent_selector.select_agents(alert_dicts, metric_dicts, threshold=60)

        # NARRATIVE: Agent selection
        terminal_logger.add_log(
            f"Orchestrator selected {len(agents_involved)} agents for this incident",
            "ORCHESTRATOR"
        )

        # PHASE 1: Update processing state to 'analyzing'
        if incident_id:
            kb.update_incident_processing_state(incident_id, 'analyzing')
            kb.add_timeline_event(incident_id, {
                'agent': 'Orchestrator',
                'event': 'Started analysis',
                'details': {'alerts_count': len(alerts)}
            })

        # PERCEPTION
        # NARRATIVE: Perception phase
        terminal_logger.add_log(
            f"Perception phase: Analyzing {len(alerts)} alerts" + (f" and {len(metrics)} metrics" if metrics else ""),
            "PERCEPTION"
        )

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

        # REASONING (delegate to selected specialist agents only)
        from agents.alert_ops import analyze_alert_stream_with_memory
        from agents.predictive_ops import analyze_metrics

        alert_analysis = None
        prediction = None

        # AlertOps: Always called if selected (correlation baseline)
        if "AlertOps" in agents_involved:
            try:
                if incident_id:
                    kb.add_timeline_event(incident_id, {
                        'agent': 'AlertOps',
                        'event': 'Correlating and analyzing alerts',
                        'details': {'alerts_count': len(alerts)}
                    })

                terminal_logger.add_log(
                    f"AlertOps analyzing {len(alerts)} alerts for correlation patterns",
                    "ALERTOPS"
                )

                alert_analysis = analyze_alert_stream_with_memory(alerts)

                terminal_logger.add_log(
                    "AlertOps completed correlation analysis",
                    "ALERTOPS"
                )

                # Track action for agent status display
                if incident_id:
                    kb.add_incident_action(incident_id, {
                        'type': 'alert_correlation',
                        'agent': 'AlertOps',
                        'description': f'Correlated {len(alerts)} alerts',
                        'status': 'completed'
                    })
            except Exception as e:
                terminal_logger.add_log(
                    f"AlertOps failed: {str(e)} - continuing with degraded analysis",
                    "ALERTOPS"
                )
                if incident_id:
                    kb.add_timeline_event(incident_id, {
                        'agent': 'AlertOps',
                        'event': 'Agent invocation failed - continuing with other agents',
                        'details': {'error': str(e)}
                    })
                # Don't mark as failed or re-raise - continue with other agents
                alert_analysis = None  # Set to None to indicate failure

        # PredictiveOps: Only if selected AND metrics available
        if "PredictiveOps" in agents_involved and metrics:
            try:
                if incident_id:
                    kb.add_timeline_event(incident_id, {
                        'agent': 'PredictiveOps',
                        'event': 'Performing predictive analysis on metrics',
                        'details': {'metrics_count': len(metrics)}
                    })

                terminal_logger.add_log(
                    f"PredictiveOps analyzing {len(metrics)} metrics for trend forecasting",
                    "PREDICTIVEOPS"
                )

                prediction = analyze_metrics(metrics)

                terminal_logger.add_log(
                    "PredictiveOps completed predictive analysis",
                    "PREDICTIVEOPS"
                )

                # Track action for agent status display
                if incident_id:
                    kb.add_incident_action(incident_id, {
                        'type': 'predictive_analysis',
                        'agent': 'PredictiveOps',
                        'description': f'Analyzed {len(metrics)} metrics for trends',
                        'status': 'completed'
                    })
            except Exception as e:
                terminal_logger.add_log(
                    f"PredictiveOps failed: {str(e)} - continuing with degraded analysis",
                    "PREDICTIVEOPS"
                )
                if incident_id:
                    kb.add_timeline_event(incident_id, {
                        'agent': 'PredictiveOps',
                        'event': 'Agent invocation failed - continuing with other agents',
                        'details': {'error': str(e)}
                    })
                # Don't mark as failed or re-raise - continue with other agents
                prediction = None  # Set to None to indicate failure

        # Track PatchOps and TaskOps if selected (even if not explicitly invoked)
        if "PatchOps" in agents_involved and incident_id:
            terminal_logger.add_log(
                "PatchOps evaluating patch requirements",
                "PATCHOPS"
            )
            kb.add_incident_action(incident_id, {
                'type': 'patch_evaluation',
                'agent': 'PatchOps',
                'description': 'Evaluated patch requirements for incident',
                'status': 'completed'
            })

        if "TaskOps" in agents_involved and incident_id:
            terminal_logger.add_log(
                "TaskOps assessing automation opportunities",
                "TASKOPS"
            )
            kb.add_incident_action(incident_id, {
                'type': 'automation_assessment',
                'agent': 'TaskOps',
                'description': 'Assessed automation opportunities',
                'status': 'completed'
            })

        # SYNTHESIS
        # NARRATIVE: Synthesis phase
        terminal_logger.add_log(
            f"Orchestrator synthesizing findings from {len(agents_involved)} agents",
            "SYNTHESIS"
        )

        synthesis = self._synthesize(alert_analysis, prediction, learned)

        # NARRATIVE: Root cause identified
        terminal_logger.add_log(
            "Orchestrator identified root cause and remediation strategy",
            "ORCHESTRATOR"
        )

        # Track Orchestrator action for agent status display
        if incident_id:
            kb.add_incident_action(incident_id, {
                'type': 'synthesis',
                'agent': 'Orchestrator',
                'description': f'Synthesized findings from {len(agents_involved)} agents',
                'status': 'completed'
            })

        # Prepare full alert details for storage
        alert_details = [
            {
                "alert_id": a.alert_id,
                "title": a.title,
                "host": a.host,
                "severity": a.severity.value,
                "timestamp": a.timestamp.isoformat() if hasattr(a.timestamp, 'isoformat') else str(a.timestamp)
            }
            for a in alerts
        ]

        # LEARN: Store for future reference
        # Update incident with analysis results and all agents that participated
        incident_data = {
            "incident_id": incident_id or str(uuid.uuid4()),
            "alerts": alert_details,
            "root_cause": str(synthesis),  # FIX: Store full synthesis, don't truncate
            "outcome": "pending",
            "agents_involved": agents_involved  # All 5 agents analyzed this incident
        }

        if not incident_id:
            incident_id = kb.store_incident(incident_data)
        else:
            # Update existing incident with agents_involved
            existing = kb.get_incident(incident_id)
            if existing:
                existing['agents_involved'] = agents_involved
                existing['root_cause'] = str(synthesis)  # FIX: Store full synthesis
                kb.incident_memory[incident_id] = existing

        # PHASE 1 TASK 1.2: Mark processing as complete
        if incident_id:
            kb.update_incident_processing_state(incident_id, 'resolved')
            kb.add_timeline_event(incident_id, {
                'agent': 'Orchestrator',
                'event': 'Processing complete',
                'details': {'status': 'resolved', 'agents_count': len(agents_involved)}
            })

        # PHASE C: Record agent selection for learning
        keywords = agent_selector._extract_keywords(alert_dicts)
        outcome_quality = 0.8  # Default good outcome (can be enhanced with actual success metrics)
        kb.record_agent_selection(keywords, agents_involved, outcome_quality)

        # MEMORY
        self._log_decision(incident_id, synthesis)

        return {
            "incident_id": incident_id,
            "perception": alert_perception,
            "learned_patterns": learned["successful_patterns"],
            "synthesis": synthesis
        }

    def _synthesize(self, alert_analysis, prediction, learned):
        """Synthesize findings using Anthropic SDK"""
        import json

        # Normalize alert analysis
        alert_str = str(alert_analysis)[:300] if alert_analysis else 'Alert analysis unavailable - agent failed'

        # Normalize prediction + optional ETS block
        prediction_summary = 'N/A'
        ets_block = None
        if isinstance(prediction, dict):
            prediction_summary = (prediction.get("text") or prediction.get("summary") or str(prediction))[:500]
            ets_block = prediction.get("ets")
        elif prediction:
            prediction_summary = str(prediction)[:500]

        ets_snippet = ""
        if ets_block and ets_block.get("series"):
            try:
                ets_snippet = json.dumps({
                    "series": ets_block.get("series", [])[:2],
                    "top_anomalies": ets_block.get("top_anomalies", [])[:3],
                    "horizon": ets_block.get("horizon")
                })[:600]
            except Exception:
                ets_snippet = str(ets_block)[:400]

        context = f"""
Alert Analysis: {alert_str}
Prediction: {prediction_summary}
ETS Forecasts: {ets_snippet or 'none'}
Learned Patterns: {learned['successful_patterns']} successful patterns in KB
"""
        prompt = f"Synthesize unified response:\n{context}"

        # Call Bedrock API
        response = client.messages.create(
            model=os.getenv("STRANDS_MODEL_ID", "claude-sonnet-4-20250514"),
            max_tokens=2048,
            system=ORCHESTRATOR_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.content[0].text

    def _log_decision(self, incident_id, synthesis):
        self.audit_log.append({
            "incident_id": incident_id,
            "decision": str(synthesis)[:150]
        })

# Global instance
enhanced_orchestrator = EnhancedOrchestrator()
