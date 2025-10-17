from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AlertStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

class Alert(BaseModel):
    alert_id: str
    title: str
    description: str
    severity: Severity
    source: str  # RMM, SIEM, CloudWatch
    host: str
    timestamp: datetime
    status: AlertStatus = AlertStatus.OPEN
    tags: List[str] = []
    metadata: dict = {}

class Metric(BaseModel):
    metric_id: str
    host: str
    metric_name: str  # cpu_usage, memory_usage, disk_usage, network_errors
    value: float
    timestamp: datetime
    unit: str = "percent"

class CorrelationResult(BaseModel):
    primary_alert_id: str
    related_alert_ids: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    root_cause: str
    reasoning: List[str]
    suppressed_count: int