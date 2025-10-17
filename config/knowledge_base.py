import boto3
from datetime import datetime
from typing import Dict, List, Optional
import json
import uuid

class KnowledgeBase:
    """Persistent storage for agent memory and learning"""
    
    def __init__(self, use_local=True):
        if use_local:
            # Local simulation for development
            self.incident_memory = {}
            self.pattern_library = {}
            self.agent_knowledge = {}
            self.local_mode = True
        else:
            self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            self.incident_table = self.dynamodb.Table('opsforge-incident-memory')
            self.pattern_table = self.dynamodb.Table('opsforge-pattern-library')
            self.knowledge_table = self.dynamodb.Table('opsforge-agent-knowledge')
            self.local_mode = False
    
    # Incident Memory
    def store_incident(self, incident_data: Dict) -> str:
        """Store incident with agent decisions"""
        incident_id = incident_data.get('incident_id') or f"INC-{uuid.uuid4().hex[:8]}"
        
        record = {
            'incident_id': incident_id,
            'timestamp': int(datetime.now().timestamp()),
            'alerts': incident_data.get('alerts', []),
            'root_cause': incident_data.get('root_cause'),
            'actions_taken': incident_data.get('actions_taken', []),
            'outcome': incident_data.get('outcome', 'pending'),
            'agents_involved': incident_data.get('agents_involved', []),
            'metadata': incident_data.get('metadata', {})
        }
        
        if self.local_mode:
            self.incident_memory[incident_id] = record
        else:
            self.incident_table.put_item(Item=record)
        
        return incident_id
    
    def get_incident(self, incident_id: str) -> Optional[Dict]:
        """Retrieve incident by ID"""
        if self.local_mode:
            return self.incident_memory.get(incident_id)
        else:
            response = self.incident_table.get_item(Key={'incident_id': incident_id})
            return response.get('Item')
    
    def get_similar_incidents(self, keywords: List[str], limit: int = 5) -> List[Dict]:
        """Find similar past incidents"""
        if self.local_mode:
            results = []
            for inc in self.incident_memory.values():
                root_cause = inc.get('root_cause', '').lower()
                if any(kw.lower() in root_cause for kw in keywords):
                    results.append(inc)
            return results[:limit]
        else:
            # DynamoDB scan with filter (simplified)
            response = self.incident_table.scan(Limit=limit)
            return response.get('Items', [])
    
    # Pattern Library
    def store_pattern(self, pattern_type: str, pattern_data: Dict) -> str:
        """Store learned correlation/prediction pattern"""
        pattern_id = f"PAT-{uuid.uuid4().hex[:8]}"
        
        record = {
            'pattern_id': pattern_id,
            'pattern_type': pattern_type,  # 'correlation', 'prediction', 'remediation'
            'confidence': pattern_data.get('confidence', 0.0),
            'occurrences': pattern_data.get('occurrences', 1),
            'success_rate': pattern_data.get('success_rate', 0.0),
            'details': pattern_data.get('details', {}),
            'created_at': int(datetime.now().timestamp())
        }
        
        if self.local_mode:
            self.pattern_library[pattern_id] = record
        else:
            self.pattern_table.put_item(Item=record)
        
        return pattern_id
    
    def get_patterns_by_type(self, pattern_type: str) -> List[Dict]:
        """Get all patterns of specific type"""
        if self.local_mode:
            return [p for p in self.pattern_library.values() 
                   if p.get('pattern_type') == pattern_type]
        else:
            response = self.pattern_table.query(
                IndexName='type-index',
                KeyConditionExpression='pattern_type = :pt',
                ExpressionAttributeValues={':pt': pattern_type}
            )
            return response.get('Items', [])
    
    # Agent Knowledge
    def store_agent_knowledge(self, agent_name: str, key: str, value: Dict):
        """Store agent-specific knowledge"""
        if self.local_mode:
            if agent_name not in self.agent_knowledge:
                self.agent_knowledge[agent_name] = {}
            self.agent_knowledge[agent_name][key] = value
        else:
            self.knowledge_table.put_item(Item={
                'agent_name': agent_name,
                'knowledge_key': key,
                'value': json.dumps(value),
                'updated_at': int(datetime.now().timestamp())
            })
    
    def get_agent_knowledge(self, agent_name: str, key: str) -> Optional[Dict]:
        """Retrieve agent knowledge"""
        if self.local_mode:
            return self.agent_knowledge.get(agent_name, {}).get(key)
        else:
            response = self.knowledge_table.get_item(
                Key={'agent_name': agent_name, 'knowledge_key': key}
            )
            item = response.get('Item')
            if item:
                return json.loads(item['value'])
            return None
    
    def update_pattern_stats(self, pattern_id: str, success: bool):
        """Update pattern success rate based on outcome"""
        if self.local_mode:
            pattern = self.pattern_library.get(pattern_id)
            if pattern:
                pattern['occurrences'] += 1
                successes = pattern['success_rate'] * (pattern['occurrences'] - 1)
                if success:
                    successes += 1
                pattern['success_rate'] = successes / pattern['occurrences']
        # DynamoDB implementation would use UpdateItem

# Global instance
kb = KnowledgeBase(use_local=True)