import random
import time
from datetime import datetime, timedelta
from typing import List
from data.models import Alert, Severity, AlertStatus
import uuid

class AlertSimulator:
    """Generates realistic IT alerts with diverse incident patterns"""

    ALERT_PATTERNS = {
        "database_cascade": {
            "root": "Database server unresponsive",
            "related": ["Web server connection timeout", "API Gateway 504 errors", "Connection pool exhausted", "High CPU on db-server"],
            "hosts": ["db-prod-01", "web-staging-19", "api-gateway-03"],
            "severity": Severity.CRITICAL
        },
        "memory_leak": {
            "root": "Memory exhausted on application server",
            "related": ["Application slowness reported", "Swap usage at 95%", "OOM killer triggered", "Service restart detected"],
            "hosts": ["app-server-12", "app-server-13"],
            "severity": Severity.HIGH
        },
        "cpu_spike": {
            "root": "CPU usage sustained above 95%",
            "related": ["Process consuming excessive CPU", "Thread pool exhaustion", "Request queue backing up", "Response time degraded"],
            "hosts": ["app-server-05", "worker-node-03"],
            "severity": Severity.HIGH
        },
        "disk_full": {
            "root": "Disk space critical on volume",
            "related": ["Log files filling partition", "Temp directory out of space", "Database writes failing", "Application errors: no space left"],
            "hosts": ["file-server-01", "db-prod-02"],
            "severity": Severity.CRITICAL
        },
        "network_partition": {
            "root": "Network partition detected between datacenters",
            "related": ["Replication lag increasing", "Split-brain condition possible", "Heartbeat timeout", "Failover triggered"],
            "hosts": ["dc1-router-01", "dc2-router-01"],
            "severity": Severity.CRITICAL
        },
        "ssl_expiry": {
            "root": "SSL certificate expired",
            "related": ["HTTPS connections failing", "Browser warnings reported", "API authentication errors", "Certificate validation failed"],
            "hosts": ["web-lb-01", "api-gateway-01"],
            "severity": Severity.HIGH
        },
        "backup_failure": {
            "root": "Scheduled backup job failed",
            "related": ["Backup storage unreachable", "Incremental backup missing", "Retention policy violation", "Backup verification failed"],
            "hosts": ["backup-server-01", "nas-prod-01"],
            "severity": Severity.MEDIUM
        },
        "security_breach": {
            "root": "Suspicious authentication attempts detected",
            "related": ["Multiple failed logins", "Unusual geographic access", "Privilege escalation attempt", "Security policy violation"],
            "hosts": ["auth-server-01", "vpn-gateway-02"],
            "severity": Severity.CRITICAL
        },
        "container_crash": {
            "root": "Container restart loop detected",
            "related": ["Pod eviction due to resource limits", "Image pull errors", "Liveness probe failing", "Container exit code 137"],
            "hosts": ["k8s-node-07", "k8s-node-08"],
            "severity": Severity.HIGH
        },
        "dns_failure": {
            "root": "DNS resolution failures increasing",
            "related": ["Name server timeout", "DNS cache poisoning suspected", "NXDOMAIN responses spiking", "Recursive query failures"],
            "hosts": ["dns-server-01", "dns-server-02"],
            "severity": Severity.HIGH
        },
        "load_balancer_down": {
            "root": "Load balancer health check failing",
            "related": ["Backend pool empty", "Health probe timeout", "SSL handshake errors", "Connection refused from backends"],
            "hosts": ["lb-prod-01", "web-server-05", "web-server-06"],
            "severity": Severity.CRITICAL
        },
        "patch_reboot_required": {
            "root": "Critical security patch installed, reboot pending",
            "related": ["System uptime exceeds policy", "Kernel update requires restart", "Services running on old libraries", "Vulnerability window open"],
            "hosts": ["win-server-11", "win-server-12"],
            "severity": Severity.MEDIUM
        },
        "api_rate_limit": {
            "root": "API rate limit exceeded",
            "related": ["429 Too Many Requests errors", "Client retry storm detected", "Throttling policy triggered", "Quota exhausted"],
            "hosts": ["api-gateway-02", "api-backend-03"],
            "severity": Severity.MEDIUM
        },
        "cache_miss_storm": {
            "root": "Cache hit ratio dropped below threshold",
            "related": ["Database query load spiking", "Cache eviction rate high", "Redis memory pressure", "Backend latency increasing"],
            "hosts": ["redis-cluster-01", "db-read-replica-01"],
            "severity": Severity.HIGH
        },
        "storage_latency": {
            "root": "Storage I/O latency spike detected",
            "related": ["Disk queue depth high", "IOPS limit reached", "Read/write timeouts", "Database checkpoint stalled"],
            "hosts": ["san-storage-01", "db-prod-03"],
            "severity": Severity.HIGH
        },
        "service_dependency_failure": {
            "root": "External service dependency unavailable",
            "related": ["Third-party API timeout", "Circuit breaker opened", "Fallback mechanism activated", "Degraded mode enabled"],
            "hosts": ["integration-server-01", "middleware-proxy-01"],
            "severity": Severity.MEDIUM
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