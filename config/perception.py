from typing import Dict, List
from datetime import datetime
from config.knowledge_base import kb

class AgentPerception:
    """Unified perception layer for all agents"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.context_window = []
    
    def perceive_alerts(self, alerts: List[Dict]) -> Dict:
        """Process incoming alerts with context"""
        # Aggregate alert data
        perception = {
            "total_alerts": len(alerts),
            "severity_breakdown": self._count_by_severity(alerts),
            "affected_hosts": list(set(a.get("host") for a in alerts)),
            "time_window": self._get_time_window(alerts),
            "sources": list(set(a.get("source") for a in alerts))
        }
        
        # Add historical context
        keywords = self._extract_keywords(alerts)
        similar = kb.get_similar_incidents(keywords, limit=3)
        perception["historical_context"] = {
            "similar_incidents": len(similar),
            "common_root_causes": [s.get("root_cause") for s in similar[:2]]
        }
        
        self.context_window.append({
            "type": "alerts",
            "data": perception,
            "timestamp": datetime.now()
        })
        
        return perception
    
    def perceive_metrics(self, metrics: List[Dict]) -> Dict:
        """Process metric streams"""
        perception = {
            "data_points": len(metrics),
            "hosts": list(set(m.get("host") for m in metrics)),
            "metric_types": list(set(m.get("metric_name") for m in metrics)),
            "trends": self._analyze_trends(metrics)
        }
        
        self.context_window.append({
            "type": "metrics",
            "data": perception,
            "timestamp": datetime.now()
        })
        
        return perception
    
    def get_context(self) -> List[Dict]:
        """Get recent context window"""
        return self.context_window[-10:]  # Last 10 perceptions
    
    def _count_by_severity(self, alerts):
        counts = {}
        for a in alerts:
            sev = a.get("severity", "unknown")
            counts[sev] = counts.get(sev, 0) + 1
        return counts
    
    def _get_time_window(self, alerts):
        timestamps = [a.get("timestamp") for a in alerts if a.get("timestamp")]
        if not timestamps:
            return None
        return {
            "start": min(timestamps).isoformat() if timestamps else None,
            "end": max(timestamps).isoformat() if timestamps else None
        }
    
    def _extract_keywords(self, alerts):
        keywords = []
        for a in alerts:
            title = a.get("title", "")
            keywords.extend(title.split()[:3])  # First 3 words
        return list(set(keywords))
    
    def _analyze_trends(self, metrics):
        by_metric = {}
        for m in metrics:
            name = m.get("metric_name")
            if name not in by_metric:
                by_metric[name] = []
            by_metric[name].append(m.get("value", 0))
        
        trends = {}
        for name, values in by_metric.items():
            if len(values) >= 2:
                trend = "increasing" if values[-1] > values[0] else "decreasing"
                trends[name] = trend
        return trends