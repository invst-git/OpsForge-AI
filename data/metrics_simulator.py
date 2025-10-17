import random
from datetime import datetime, timedelta
from typing import List
import uuid
from data.models import Metric

class MetricsSimulator:
    """Generates realistic system metrics with failure patterns"""
    
    def generate_normal_metrics(self, host: str, duration_hours: int = 1) -> List[Metric]:
        """Generate normal baseline metrics"""
        metrics = []
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=duration_hours)
        
        # Generate metrics every 5 minutes
        current_time = start_time
        while current_time <= end_time:
            # CPU: 20-40% normal
            metrics.append(Metric(
                metric_id=f"MET-{uuid.uuid4().hex[:8]}",
                host=host,
                metric_name="cpu_usage",
                value=random.uniform(20, 40),
                timestamp=current_time,
                unit="percent"
            ))
            
            # Memory: 40-60% normal
            metrics.append(Metric(
                metric_id=f"MET-{uuid.uuid4().hex[:8]}",
                host=host,
                metric_name="memory_usage",
                value=random.uniform(40, 60),
                timestamp=current_time,
                unit="percent"
            ))
            
            # Disk: 50-70% normal
            metrics.append(Metric(
                metric_id=f"MET-{uuid.uuid4().hex[:8]}",
                host=host,
                metric_name="disk_usage",
                value=random.uniform(50, 70),
                timestamp=current_time,
                unit="percent"
            ))
            
            current_time += timedelta(minutes=5)
        
        return metrics
    
    def generate_failure_pattern(self, host: str, pattern: str = "cpu_spike") -> List[Metric]:
        """Generate metrics showing failure pattern"""
        metrics = []
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=2)
        
        current_time = start_time
        step = 0
        
        while current_time <= end_time:
            if pattern == "cpu_spike":
                # CPU gradually increases to 95%+
                cpu = min(95, 30 + (step * 3))
                memory = random.uniform(40, 60)
                
            elif pattern == "memory_leak":
                # Memory gradually increases
                cpu = random.uniform(30, 50)
                memory = min(95, 40 + (step * 2.5))
                
            elif pattern == "disk_full":
                # Disk usage climbs to critical
                cpu = random.uniform(20, 40)
                memory = random.uniform(40, 60)
                disk = min(95, 60 + (step * 2))  # Add this

            
            metrics.append(Metric(
                metric_id=f"MET-{uuid.uuid4().hex[:8]}",
                host=host,
                metric_name="cpu_usage",
                value=cpu,
                timestamp=current_time,
                unit="percent"
            ))
            
            metrics.append(Metric(
                metric_id=f"MET-{uuid.uuid4().hex[:8]}",
                host=host,
                metric_name="memory_usage",
                value=memory,
                timestamp=current_time,
                unit="percent"
            ))
            
            current_time += timedelta(minutes=5)
            step += 1
        
        return metrics