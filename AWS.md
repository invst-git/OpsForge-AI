## OpsForge AI AWS Cloud Architecture
Following is the AWS cloud deployment architecture of OpsForge AI, covering both serverless Lambda deployment [1a] and full EC2 stack deployment [2a]. It shows the integration with AWS Bedrock for LLM capabilities [3b], DynamoDB persistence [4a], and the agent orchestration flow [5a] that coordinates specialist agents for incident analysis. The serverless deployment uses API Gateway [6a] and EventBridge [6c] for event-driven processing, while the EC2 deployment provides a complete stack with nginx reverse proxy [2b] and systemd services.
### 1. Serverless Event Processing Flow
AWS Lambda functions handle incoming events and route them to the orchestrator for analysis
### 1a. Lambda Function Definition (`template.yaml:11`)
Defines the main Lambda function for event-driven processing
```text
Resources:
  OpsForgeFunction:
    Type: AWS::Serverless::Function
```
### 1b. Lambda Entry Point (`lambda_handler.py:7`)
Main Lambda handler that processes incoming events
```text
def lambda_handler(event, context):
    """AWS Lambda entry point for OpsForge AI"""
```
### 1c. Event Type Routing (`lambda_handler.py:14`)
Routes events to appropriate handlers based on type
```text
if event_type == 'alerts':
        return handle_alerts(event.get('data', []))
    elif event_type == 'metrics':
        return handle_metrics(event.get('data', []))
    elif event_type == 'incident':
        return handle_incident(event.get('alerts', []), event.get('metrics', []))
```
### 1d. Orchestrator Invocation (`lambda_handler.py:29`)
Delegates incident analysis to the EnhancedOrchestrator
```text
result = orchestrator.handle_incident(alerts, metrics=None)
```
### 2. EC2 Full-Stack Deployment
Complete application stack running on EC2 with nginx reverse proxy and systemd services
### 2a. EC2 Instance Launch (`EC2_COMMANDS.txt:5`)
Launches t3.medium Ubuntu instance for the full stack
```text
aws ec2 run-instances \
    --image-id ami-0e001c9271cf7f3b9 \
    --instance-type t3.medium
```
### 2b. Nginx Reverse Proxy (`ec2_setup.sh:25`)
Configures nginx to serve frontend and proxy API requests
```text
server {
    listen 80;
    # Backend API proxy
    location /api/ {
        proxy_pass http://localhost:8000/api/;
```
### 2c. Backend Systemd Service (`ec2_setup.sh:67`)
Systemd service definition for FastAPI backend
```text
ExecStart=/usr/bin/python3 backend_api.py
```
### 2d. Data Generator Service (`ec2_setup.sh:92`)
Systemd service for continuous incident simulation
```text
ExecStart=/usr/bin/python3 live_data_generator.py
```
### 3. AWS Bedrock LLM Integration
Integration with AWS Bedrock for LLM-powered reasoning and synthesis across all agents
### 3a. Bedrock Client Initialization (`bedrock_client.py:21`)
Creates boto3 client for AWS Bedrock runtime
```text
self.bedrock_runtime = boto3.client(
        service_name='bedrock-runtime',
        region_name=self.region_name
    )
```
### 3b. Model Invocation (`bedrock_client.py:84`)
Calls Bedrock API with rate limiting and retry logic
```text
response = self.bedrock_runtime.invoke_model(
            modelId=model,
            body=json.dumps(request_body)
        )
```
### 3c. Orchestrator LLM Call (`orchestrator.py:316`)
EnhancedOrchestrator synthesizes findings using Claude
```text
response = client.messages.create(
            model=os.getenv("STRANDS_MODEL_ID", "claude-sonnet-4-20250514"),
            max_tokens=2048,
            system=ORCHESTRATOR_SYSTEM_PROMPT
```
### 3d. IAM Permissions (`template.yaml:31`)
Lambda IAM policy permissions for Bedrock access
```text
- bedrock:InvokeModel
- bedrock:InvokeModelWithResponseStream
```
### 4. DynamoDB Persistence Layer
DynamoDB integration for persistent storage of incidents, patterns, and agent knowledge
### 4a. Incident Memory Table (`dynamodb_schema.py:7`)
DynamoDB table schema for incident storage
```text
INCIDENT_MEMORY_TABLE = {
    'TableName': 'opsforge-incident-memory',
    'KeySchema': [
        {'AttributeName': 'incident_id', 'KeyType': 'HASH'}
    ]
```
### 4b. Pattern Library Table (`dynamodb_schema.py:26`)
Stores learned patterns for future reference
```text
PATTERN_LIBRARY_TABLE = {
    'TableName': 'opsforge-pattern-library'
```
### 4c. Agent Knowledge Table (`dynamodb_schema.py:45`)
Stores agent-specific knowledge and learnings
```text
AGENT_KNOWLEDGE_TABLE = {
    'TableName': 'opsforge-agent-knowledge',
    'KeySchema': [
        {'AttributeName': 'agent_name', 'KeyType': 'HASH'},
        {'AttributeName': 'knowledge_key', 'KeyType': 'RANGE'}
    ]
```
### 4d. DynamoDB Resource (`dynamodb_schema.py:4`)
Initializes DynamoDB resource for table operations
```text
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
```
### 5. Agent Orchestration Flow
EnhancedOrchestrator coordinates specialist agents for incident analysis and response
### 5a. Intelligent Agent Selection (`orchestrator.py:61`)
AgentSelector chooses relevant agents based on incident content
```text
agents_involved = agent_selector.select_agents(alert_dicts, metric_dicts, threshold=60)
```
### 5b. AlertOps Invocation (`orchestrator.py:110`)
Calls AlertOps for alert correlation analysis
```text
if "AlertOps" in agents_involved:
        alert_analysis = analyze_alert_stream_with_memory(alerts)
```
### 5c. PredictiveOps Invocation (`orchestrator.py:154`)
Calls PredictiveOps for metric trend analysis
```text
if "PredictiveOps" in agents_involved and metrics:
        prediction = analyze_metrics(metrics)
```
### 5d. Result Synthesis (`orchestrator.py:229`)
Combines all agent analyses into unified response
```text
synthesis = self._synthesize(alert_analysis, prediction, learned)
```
### 6. API Gateway and Event Triggers
Serverless event routing through API Gateway REST endpoints and EventBridge rules
### 6a. API Gateway Definition (`template.yaml:49`)
Defines REST API for external access
```text
OpsForgeApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: prod
```
### 6b. Analyze Endpoint (`template.yaml:75`)
POST endpoint for incident analysis requests
```text
Path: /analyze
        Method: POST
```
### 6c. Alert Event Rule (`template.yaml:36`)
EventBridge rule for alert events
```text
AlertEvent:
          Type: EventBridgeRule
          Properties:
            Pattern:
              source:
                - opsforge.alerts
```
### 6d. Metric Event Rule (`template.yaml:42`)
EventBridge rule for metric events
```text
MetricEvent:
          Type: EventBridgeRule
          Properties:
            Pattern:
              source:
                - opsforge.metrics
```