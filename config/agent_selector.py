"""Intelligent agent selection based on incident characteristics"""

from typing import List, Dict, Tuple, Optional
from config.bedrock_client import BedrockClient
import os
import json

client = BedrockClient(region_name=os.getenv("AWS_REGION", "us-east-1"))

class AgentSelector:
    """Determines which agents are relevant for a given incident"""

    # Agent capability descriptions for LLM reasoning
    AGENT_CAPABILITIES = {
        "AlertOps": {
            "expertise": "Alert correlation, pattern detection, noise reduction",
            "keywords": ["alert", "correlation", "duplicate", "similar", "related", "cluster"],
            "use_when": "Multiple alerts need correlation or pattern analysis"
        },
        "PredictiveOps": {
            "expertise": "Trend analysis, forecasting, capacity planning, anomaly detection",
            "keywords": ["trend", "forecast", "predict", "spike", "increase", "pattern", "metric", "usage"],
            "use_when": "Metrics show trends, spikes, or need future predictions"
        },
        "PatchOps": {
            "expertise": "Patch deployment, update management, rollback, canary testing",
            "keywords": ["patch", "update", "KB", "hotfix", "version", "upgrade", "reboot", "install"],
            "use_when": "Incident involves patches, updates, or version issues"
        },
        "TaskOps": {
            "expertise": "Task automation, workflow execution, repetitive operations",
            "keywords": ["automate", "task", "workflow", "restart", "cleanup", "reset", "routine"],
            "use_when": "Incident requires automated tasks or repetitive actions"
        }
    }

    def __init__(self):
        self.selection_cache = {}

    def calculate_keyword_relevance(self, agent_name: str, alerts: List[Dict], metrics: List[Dict] = None) -> int:
        """Calculate keyword-based relevance score (0-40 points)"""
        if agent_name not in self.AGENT_CAPABILITIES:
            return 0

        keywords = self.AGENT_CAPABILITIES[agent_name]["keywords"]
        score = 0

        # Check alert titles and descriptions
        for alert in alerts:
            text = f"{alert.get('title', '')} {alert.get('description', '')}".lower()
            for keyword in keywords:
                if keyword in text:
                    score += 5
                    break

        # Check metric names if available
        if metrics:
            for metric in metrics[:10]:  # Sample first 10
                metric_name = metric.get('metric_name', '').lower()
                for keyword in keywords:
                    if keyword in metric_name:
                        score += 3
                        break

        return min(score, 40)

    def select_agents_llm(self, alerts: List[Dict], metrics: List[Dict] = None) -> Dict[str, int]:
        """Use LLM to intelligently select agents with confidence scores"""

        # Prepare incident summary
        alert_summary = "\n".join([
            f"- [{a.get('severity', 'UNKNOWN')}] {a.get('title', 'No title')}"
            for a in alerts[:5]
        ])

        metric_summary = ""
        if metrics:
            metric_summary = f"\nMetrics: {len(metrics)} data points available"

        # Build prompt for agent selection
        prompt = f"""Analyze this IT incident and determine which specialist agents should handle it.

INCIDENT DETAILS:
{alert_summary}{metric_summary}

AVAILABLE AGENTS:
1. AlertOps - {self.AGENT_CAPABILITIES['AlertOps']['use_when']}
2. PredictiveOps - {self.AGENT_CAPABILITIES['PredictiveOps']['use_when']}
3. PatchOps - {self.AGENT_CAPABILITIES['PatchOps']['use_when']}
4. TaskOps - {self.AGENT_CAPABILITIES['TaskOps']['use_when']}

Return ONLY a JSON object with agent names and relevance scores (0-100):
{{"AlertOps": 85, "PredictiveOps": 70, "PatchOps": 10, "TaskOps": 60}}

Score 80-100: Highly relevant, critical for resolution
Score 60-79: Relevant, should contribute
Score 40-59: Somewhat relevant, optional
Score 0-39: Not relevant, skip

Rules:
- AlertOps is almost always relevant (correlation baseline)
- PredictiveOps only if metrics available and trending issues
- PatchOps only for patch/update related issues
- TaskOps for automation opportunities

JSON only, no explanation:"""

        try:
            response = client.messages.create(
                model=os.getenv("STRANDS_MODEL_ID", "claude-sonnet-4-20250514"),
                max_tokens=256,
                temperature=0.3,
                system="You are an expert IT operations analyst. Return only valid JSON.",
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()

            # Extract JSON from response
            if "{" in response_text:
                json_start = response_text.index("{")
                json_end = response_text.rindex("}") + 1
                json_str = response_text[json_start:json_end]
                scores = json.loads(json_str)

                # Validate scores
                validated = {}
                for agent in ["AlertOps", "PredictiveOps", "PatchOps", "TaskOps"]:
                    validated[agent] = max(0, min(100, scores.get(agent, 0)))

                return validated

        except Exception as e:
            # Fallback to keyword-based scoring
            import logging
            logging.warning(f"LLM agent selection failed: {e}. Falling back to keyword-based heuristic.")

        # Fallback: Use keyword-based heuristic
        return self._fallback_selection(alerts, metrics)

    def _fallback_selection(self, alerts: List[Dict], metrics: List[Dict] = None) -> Dict[str, int]:
        """Fallback keyword-based agent selection when LLM unavailable"""
        scores = {}

        # AlertOps: Almost always relevant for correlation
        scores["AlertOps"] = 85 if len(alerts) > 1 else 70

        # PredictiveOps: Relevant if metrics available
        scores["PredictiveOps"] = 75 if metrics and len(metrics) > 10 else 30

        # Keyword-based scoring for specialized agents
        scores["PatchOps"] = self.calculate_keyword_relevance("PatchOps", alerts, metrics)
        scores["TaskOps"] = self.calculate_keyword_relevance("TaskOps", alerts, metrics)

        return scores

    def select_agents(self, alerts: List[Dict], metrics: List[Dict] = None, threshold: int = 60) -> List[str]:
        """Select agents above relevance threshold with learned pattern integration"""

        # Phase C: Check for learned patterns first
        keywords = self._extract_keywords(alerts)
        learned_suggestion = self._get_learned_suggestion(keywords)

        if learned_suggestion:
            # Use learned pattern with high confidence
            if learned_suggestion["confidence"] >= 0.85:
                return learned_suggestion["suggested_agents"]

        # Otherwise, use LLM/keyword selection
        scores = self.select_agents_llm(alerts, metrics)

        # Adaptive thresholding based on historical outcomes (safe bounds)
        adjusted_threshold = self._adjust_threshold(keywords, threshold)

        # Always include Orchestrator
        selected = ["Orchestrator"]

        # Add agents above threshold
        for agent, score in scores.items():
            if score >= adjusted_threshold:
                selected.append(agent)

        # AlertOps baseline: If no other agents selected, include AlertOps
        if len(selected) == 1:
            selected.append("AlertOps")

        return selected

    def _extract_keywords(self, alerts: List[Dict]) -> List[str]:
        """Extract keywords from alert titles"""
        keywords = []
        for alert in alerts[:3]:  # Top 3 alerts
            title_words = alert.get("title", "").split()
            # Take first meaningful word (skip common words)
            for word in title_words:
                if len(word) > 3 and word.lower() not in ["with", "from", "that", "this"]:
                    keywords.append(word)
                    break
        return keywords

    def _get_learned_suggestion(self, keywords: List[str]) -> Optional[Dict]:
        """Get learned agent suggestions from knowledge base"""
        try:
            from config.knowledge_base import kb
            return kb.get_learned_agent_suggestions(keywords, min_incidents=3)
        except Exception:
            return None

    def _adjust_threshold(self, keywords: List[str], base_threshold: int) -> int:
        """Nudge selection threshold based on historical success; safe and bounded."""
        try:
            from config.knowledge_base import kb
            stats = kb.get_agent_selection_stats(keywords, min_incidents=5)
            if not stats:
                return base_threshold

            avg_quality = stats.get("avg_quality", 0.0)
            threshold = base_threshold

            # If we see strong success, be slightly more permissive; if weak, be conservative.
            if avg_quality >= 0.75:
                threshold = max(50, base_threshold - 5)
            elif avg_quality <= 0.4:
                threshold = min(85, base_threshold + 5)

            return threshold
        except Exception:
            return base_threshold

# Global instance
agent_selector = AgentSelector()
