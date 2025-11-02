import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Table 1: Incident Memory
INCIDENT_MEMORY_TABLE = {
    'TableName': 'opsforge-incident-memory',
    'KeySchema': [
        {'AttributeName': 'incident_id', 'KeyType': 'HASH'}
    ],
    'AttributeDefinitions': [
        {'AttributeName': 'incident_id', 'AttributeType': 'S'},
        {'AttributeName': 'timestamp', 'AttributeType': 'N'}
    ],
    'GlobalSecondaryIndexes': [{
        'IndexName': 'timestamp-index',
        'KeySchema': [{'AttributeName': 'timestamp', 'KeyType': 'HASH'}],
        'Projection': {'ProjectionType': 'ALL'},
        'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    }],
    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
}

# Table 2: Pattern Library
PATTERN_LIBRARY_TABLE = {
    'TableName': 'opsforge-pattern-library',
    'KeySchema': [
        {'AttributeName': 'pattern_id', 'KeyType': 'HASH'}
    ],
    'AttributeDefinitions': [
        {'AttributeName': 'pattern_id', 'AttributeType': 'S'},
        {'AttributeName': 'pattern_type', 'AttributeType': 'S'}
    ],
    'GlobalSecondaryIndexes': [{
        'IndexName': 'type-index',
        'KeySchema': [{'AttributeName': 'pattern_type', 'KeyType': 'HASH'}],
        'Projection': {'ProjectionType': 'ALL'},
        'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    }],
    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
}

# Table 3: Agent Knowledge
AGENT_KNOWLEDGE_TABLE = {
    'TableName': 'opsforge-agent-knowledge',
    'KeySchema': [
        {'AttributeName': 'agent_name', 'KeyType': 'HASH'},
        {'AttributeName': 'knowledge_key', 'KeyType': 'RANGE'}
    ],
    'AttributeDefinitions': [
        {'AttributeName': 'agent_name', 'AttributeType': 'S'},
        {'AttributeName': 'knowledge_key', 'AttributeType': 'S'}
    ],
    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
}

def create_tables():
    """Create all DynamoDB tables"""
    tables = [INCIDENT_MEMORY_TABLE, PATTERN_LIBRARY_TABLE, AGENT_KNOWLEDGE_TABLE]
    
    for table_config in tables:
        try:
            table = dynamodb.create_table(**table_config)
            print(f"Creating {table_config['TableName']}...")
            table.wait_until_exists()
            print(f"{table_config['TableName']} ready")
        except dynamodb.meta.client.exceptions.ResourceInUseException:
            print(f"{table_config['TableName']} already exists")

if __name__ == '__main__':
    create_tables()