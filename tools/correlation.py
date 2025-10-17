from strands.tools import tool
from typing import List, Dict
from datetime import timedelta
import networkx as nx

@tool
def correlate_alerts(alerts: List[Dict]) -> Dict:
    """
    Correlate related alerts using graph analysis.
    
    Args:
        alerts: List of alert dictionaries with keys: alert_id, title, host, timestamp, severity
    
    Returns:
        Dictionary with correlation results including primary alert, related alerts, and confidence
    """
    if len(alerts) < 2:
        return {
            "primary_alert_id": alerts[0]["alert_id"] if alerts else None,
            "related_alert_ids": [],
            "confidence": 1.0,
            "root_cause": alerts[0]["title"] if alerts else "No alerts",
            "reasoning": ["Only one alert, no correlation needed"],
            "suppressed_count": 0
        }
    
    # Build correlation graph
    G = nx.Graph()
    
    for alert in alerts:
        G.add_node(alert["alert_id"], **alert)
    
    # Add edges based on correlation factors
    for i, alert1 in enumerate(alerts):
        for alert2 in alerts[i+1:]:
            score = 0.0
            reasons = []
            
            # Same host correlation
            if alert1["host"] == alert2["host"]:
                score += 0.4
                reasons.append("same_host")
            
            # Time proximity (within 60 seconds)
            time_diff = abs((alert1["timestamp"] - alert2["timestamp"]).total_seconds())
            if time_diff < 60:
                score += 0.3
                reasons.append("time_proximity")
            
            # Keyword matching
            keywords1 = set(alert1["title"].lower().split())
            keywords2 = set(alert2["title"].lower().split())
            overlap = len(keywords1 & keywords2)
            if overlap > 0:
                score += min(0.3, overlap * 0.1)
                reasons.append("keyword_match")
            
            if score > 0.5:
                G.add_edge(alert1["alert_id"], alert2["alert_id"], 
                          weight=score, reasons=reasons)
    
    # Find largest connected component (main incident cluster)
    if G.number_of_edges() > 0:
        components = list(nx.connected_components(G))
        largest = max(components, key=len)
        
        # Identify root cause (earliest alert in cluster)
        cluster_alerts = [alerts[i] for i, a in enumerate(alerts) 
                         if a["alert_id"] in largest]
        cluster_alerts.sort(key=lambda x: x["timestamp"])
        primary = cluster_alerts[0]
        
        related_ids = [a["alert_id"] for a in cluster_alerts[1:]]
        
        return {
            "primary_alert_id": primary["alert_id"],
            "related_alert_ids": related_ids,
            "confidence": 0.85,
            "root_cause": primary["title"],
            "reasoning": [
                f"Identified cluster of {len(largest)} related alerts",
                f"Primary alert: {primary['title']} on {primary['host']}",
                f"Time span: {(cluster_alerts[-1]['timestamp'] - cluster_alerts[0]['timestamp']).seconds}s"
            ],
            "suppressed_count": len(related_ids)
        }
    
    # No correlation found
    return {
        "primary_alert_id": alerts[0]["alert_id"],
        "related_alert_ids": [],
        "confidence": 0.3,
        "root_cause": "No clear correlation detected",
        "reasoning": ["Alerts appear unrelated"],
        "suppressed_count": 0
    }