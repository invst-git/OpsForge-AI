import random
import time
from datetime import datetime, timedelta
from typing import List
from data.models import Alert, Severity, AlertStatus
import uuid

class AlertSimulator:
    """Generates realistic IT alerts with correlation patterns"""
    
    ALERT_PATTERNS = {
        "database_cascade": {
            "root": "Database server unresponsive",
            "related": [
                "Web server connection timeout",
                "API Gateway 504 errors",
                "Connection pool exhausted",
                "High CPU on db-server"
            ],
            "hosts": ["db-prod-01", "web-staging-19", "api-gateway-03"],
            "severity": Severity.CRITICAL
        },
        "memory_leak": {
            "root": "Memory exhausted on application server",
            "related": [
                "Application slowness reported",
                "Swap usage at 95%",
                "OOM killer triggered",
                "Service restart detected"
            ],
            "hosts": ["app-server-12", "app-server-13"],
            "severity": Severity.HIGH
        },
        "patch_failure": {
            "root": "KB5034763 patch installation failed",
            "related": [
                "Windows Update service crashed",
                "System reboot pending",
                "Event log full",
                "Disk space critical"
            ],
            "hosts": ["win-server-08", "win-server-09", "win-server-10"],
            "severity": Severity.MEDIUM
        },
        "network_issue": {
            "root": "Network packet loss detected",
            "related": [
                "DNS resolution failures",
                "Ping timeout to gateway",
                "TCP retransmissions high",
                "Interface errors increasing"
            ],
            "hosts": ["router-01", "switch-core-02"],
            "severity": Severity.HIGH
        }
    }
    
    def generate_alert_cluster(self, pattern_name: str) -> List[Alert]:
        """Generate a cluster of correlated alerts"""
        pattern = self.ALERT_PATTERNS[pattern_name]
        base_time = datetime.now()
        alerts = []
        
        # Root alert
        root_alert = Alert(
            alert_id=f"ALT-{uuid.uuid4().hex[:8]}",
            title=pattern["root"],
            description=f"Root cause alert: {pattern['root']}",
            severity=pattern["severity"],
            source=random.choice(["RMM", "SIEM", "CloudWatch"]),
            host=pattern["hosts"][0],
            timestamp=base_time,
            tags=["auto-generated", pattern_name, "root-cause"]
        )
        alerts.append(root_alert)
        
        # Related alerts (2-10 seconds after root)
        for i, related_title in enumerate(pattern["related"]):
            related_alert = Alert(
                alert_id=f"ALT-{uuid.uuid4().hex[:8]}",
                title=related_title,
                description=f"Related to {pattern['root']}",
                severity=random.choice([pattern["severity"], Severity.MEDIUM]),
                source=random.choice(["RMM", "SIEM", "CloudWatch", "Prometheus"]),
                host=random.choice(pattern["hosts"]),
                timestamp=base_time + timedelta(seconds=random.randint(2, 10)),
                tags=["auto-generated", pattern_name, "related"],
                metadata={"correlation_hint": root_alert.alert_id}
            )
            alerts.append(related_alert)
        
        return alerts
    
    def generate_random_alert(self) -> Alert:
        """Generate a single random alert (noise)"""
        titles = [
            "Backup job completed successfully",
            "User login from new location",
            "SSL certificate expires in 30 days",
            "Disk cleanup completed",
            "Antivirus definition updated",
            "Scheduled maintenance window started"
        ]
        
        return Alert(
            alert_id=f"ALT-{uuid.uuid4().hex[:8]}",
            title=random.choice(titles),
            description="Random noise alert",
            severity=random.choice([Severity.LOW, Severity.INFO]),
            source=random.choice(["RMM", "SIEM", "Monitoring"]),
            host=f"server-{random.randint(1, 50):02d}",
            timestamp=datetime.now(),
            tags=["auto-generated", "noise"]
        )
    
    def generate_mixed_stream(self, num_clusters: int = 2, noise_count: int = 5) -> List[Alert]:
        """Generate a realistic alert stream with patterns + noise"""
        all_alerts = []
        
        # Add correlated clusters
        patterns = list(self.ALERT_PATTERNS.keys())
        for _ in range(num_clusters):
            pattern = random.choice(patterns)
            cluster = self.generate_alert_cluster(pattern)
            all_alerts.extend(cluster)
        
        # Add noise
        for _ in range(noise_count):
            all_alerts.append(self.generate_random_alert())
        
        # Sort by timestamp
        all_alerts.sort(key=lambda x: x.timestamp)
        
        return all_alerts