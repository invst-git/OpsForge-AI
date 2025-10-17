from config.knowledge_base import kb
from typing import Dict

class AgentLearning:
    """Learning from outcomes"""
    
    @staticmethod
    def record_outcome(incident_id: str, action_taken: str, outcome: str, success: bool):
        """Record incident outcome for learning"""
        incident = kb.get_incident(incident_id)
        if incident:
            incident["outcome"] = outcome
            incident["success"] = success
            kb.store_incident(incident)
        
        # Update pattern statistics
        patterns = kb.get_patterns_by_type("correlation")
        for pattern in patterns:
            if pattern.get("details", {}).get("incident_id") == incident_id:
                kb.update_pattern_stats(pattern["pattern_id"], success)
    
    @staticmethod
    def get_learned_patterns(agent_name: str, pattern_type: str) -> Dict:
        """Retrieve learned patterns for agent"""
        patterns = kb.get_patterns_by_type(pattern_type)
        
        # Filter by success rate
        successful = [p for p in patterns if p.get("success_rate", 0) > 0.7]
        
        return {
            "total_patterns": len(patterns),
            "successful_patterns": len(successful),
            "top_patterns": sorted(successful, key=lambda x: x["success_rate"], reverse=True)[:5]
        }
    
    @staticmethod
    def improve_confidence(agent_name: str, decision_type: str, was_correct: bool):
        """Adjust agent confidence based on feedback"""
        key = f"{decision_type}_confidence"
        current = kb.get_agent_knowledge(agent_name, key) or {"value": 0.5, "samples": 0}
        
        samples = current["samples"] + 1
        if was_correct:
            new_value = current["value"] + (1 - current["value"]) * 0.1
        else:
            new_value = current["value"] * 0.9
        
        kb.store_agent_knowledge(agent_name, key, {
            "value": round(new_value, 3),
            "samples": samples
        })