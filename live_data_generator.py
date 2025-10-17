import asyncio
import random
from datetime import datetime, timedelta
from data.alert_simulator import AlertSimulator
from data.metrics_simulator import MetricsSimulator
from agents.orchestrator import enhanced_orchestrator
from config.knowledge_base import kb
from config.action_executor import executor

class LiveDataGenerator:
    def __init__(self):
        self.alert_sim = AlertSimulator()
        self.metrics_sim = MetricsSimulator()
        self.running = False
        self.kill_switch_active = False
        self.patches = []
        self.patch_counter = 0
        self.metrics_cache = {
            "alertsReduced": 67.0,
            "mttrReduction": 42.0,
            "tasksAutomated": 89,
            "activeIncidents": 0,
            "patchesPending": 0,
            "upcomingRisks": 5
        }
        self.recent_actions = []
        self.incident_times = {}
        self.generation_lock = asyncio.Lock()
    
    def toggle_kill_switch(self):
        self.kill_switch_active = not self.kill_switch_active
        return self.kill_switch_active
    
    def get_kill_switch_state(self):
        return self.kill_switch_active
    
    def _get_relative_time(self, timestamp):
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except ValueError:
                return timestamp
        
        delta = datetime.now() - timestamp
        
        if delta.seconds < 60:
            return "Just now"
        elif delta.seconds < 3600:
            mins = delta.seconds // 60
            return f"{mins} min ago"
        elif delta.seconds < 86400:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
    
    def should_generate_patch(self, incident):
        alerts = incident.get('alerts', [])
        for alert in alerts:
            alert_str = str(alert).lower()
            if any(kw in alert_str for kw in ['cve', 'vulnerability', 'outdated', 'security', 'exploit']):
                return True
        return random.random() > 0.85
    
    def generate_patch_from_incident(self, incident):
        alerts = incident.get('alerts', [])
        component = "system"
        
        for alert in alerts:
            alert_str = str(alert).lower()
            if 'database' in alert_str:
                component = random.choice(['postgresql', 'mysql', 'mongodb'])
            elif 'web' in alert_str or 'http' in alert_str:
                component = random.choice(['nginx', 'apache', 'nodejs'])
            elif 'ssl' in alert_str or 'tls' in alert_str:
                component = 'openssl'
            elif 'memory' in alert_str:
                component = random.choice(['kernel', 'glibc', 'systemd'])
        
        self.patch_counter += 1
        return {
            "id": f"PLAN-{self.patch_counter:03d}",
            "name": f"{component} v{random.randint(1,3)}.{random.randint(0,25)}.{random.randint(0,10)}",
            "systems": random.randint(10, 50),
            "progress": 0,
            "status": "pending",
            "created_at": datetime.now(),
            "incident_id": incident.get('incident_id'),
            "phases": []
        }
    
    async def progress_patch(self, patch):
        if patch['status'] == 'pending':
            if random.random() > 0.5:
                patch['status'] = 'in_progress'
                patch['phases'] = [
                    {"phase": 1, "hosts": int(patch['systems'] * 0.2), "status": "running", "start_time": datetime.now()},
                    {"phase": 2, "hosts": int(patch['systems'] * 0.3), "status": "pending"},
                    {"phase": 3, "hosts": int(patch['systems'] * 0.5), "status": "pending"}
                ]
        
        elif patch['status'] == 'in_progress':
            for phase in patch['phases']:
                if phase['status'] == 'running':
                    if random.random() > 0.98:
                        patch['status'] = 'failed'
                        phase['status'] = 'failed'
                        return
                    
                    elapsed = (datetime.now() - phase.get('start_time', datetime.now())).seconds
                    if elapsed > 20:
                        phase['status'] = 'completed'
                        
                        next_phase = next((p for p in patch['phases'] if p['status'] == 'pending'), None)
                        if next_phase:
                            next_phase['status'] = 'running'
                            next_phase['start_time'] = datetime.now()
                        else:
                            patch['status'] = 'completed'
                            patch['progress'] = 100
                    break
            
            completed = sum(1 for p in patch['phases'] if p['status'] == 'completed')
            patch['progress'] = int((completed / len(patch['phases'])) * 100)
        
    async def generate_incident(self):
        # Create placeholder incident immediately (outside lock) so frontend can see it
        incident_id = None
        try:
            if self.kill_switch_active:
                print("⚠️ Kill switch active")
                return None

            patterns = ["database_cascade", "memory_leak"]
            pattern = random.choice(patterns)

            alerts = self.alert_sim.generate_alert_cluster(pattern)
            metrics = self.metrics_sim.generate_failure_pattern(
                f"host-{random.randint(1,10)}",
                random.choice(["cpu_spike", "memory_leak"])
            )

            # Store placeholder incident IMMEDIATELY so frontend can see it
            import uuid
            incident_id = f"INC-{uuid.uuid4().hex[:8]}"
            self.incident_times[incident_id] = datetime.now()

            # Create placeholder in knowledge base
            kb.store_incident({
                "incident_id": incident_id,
                "alerts": [a.alert_id for a in alerts],
                "root_cause": "Processing...",
                "agents_involved": ["Orchestrator"],
                "outcome": "pending",
                "metadata": {"status": "processing"}
            })

            print(f"✅ Created placeholder incident {incident_id} (Total incidents: {len(kb.incident_memory)})")

            # Now do the actual processing (this takes time)
            # Orchestrator will update the placeholder incident with real results
            async with self.generation_lock:
                result = enhanced_orchestrator.handle_incident_full(alerts, metrics, incident_id=incident_id)
                print(f"✅ Completed processing {incident_id} (Total incidents: {len(kb.incident_memory)})")
                
                # Generate patch with the actual incident record
                incident_record = kb.get_incident(incident_id)
                if incident_record and self.should_generate_patch(incident_record):
                    new_patch = self.generate_patch_from_incident(incident_record)
                    new_patch['incident_id'] = incident_id
                    self.patches.append(new_patch)
                    print(f"📦 Generated patch: {new_patch['name']}")

                if not self.kill_switch_active and random.random() > 0.3:
                    action_time = datetime.now()
                    action = {
                        "type": random.choice(["suppress_alerts", "restart_service", "clear_cache"]),
                        "params": {"host": f"host-{random.randint(1,10)}"},
                        "risk_level": "LOW"
                    }
                    exec_result = executor.execute_action(action)

                    self.recent_actions.insert(0, {
                        "agent": random.choice(["AlertOps", "PatchOps", "TaskOps"]),
                        "action": f"Executed {action['type']}",
                        "timestamp": action_time,
                        "relative_time": self._get_relative_time(action_time)
                    })
                    if len(self.recent_actions) > 20:
                        self.recent_actions.pop()

                self.metrics_cache["alertsReduced"] = min(70, self.metrics_cache["alertsReduced"] + random.uniform(0.1, 0.5))
                self.metrics_cache["mttrReduction"] = min(45, self.metrics_cache["mttrReduction"] + random.uniform(0.1, 0.3))
                self.metrics_cache["activeIncidents"] = len([i for i in kb.incident_memory.values() if i.get('outcome') == 'pending'])

                return result

        except Exception as e:
            print(f"Error generating incident: {e}")
            import traceback
            traceback.print_exc()
            # Clean up placeholder if we created one
            if incident_id and incident_id in kb.incident_memory:
                incident = kb.get_incident(incident_id)
                if incident and incident.get('root_cause') == "Processing...":
                    # Mark as failed instead of deleting
                    incident['root_cause'] = f"Error: {str(e)[:100]}"
                    incident['metadata'] = {"status": "failed"}
                    kb.incident_memory[incident_id] = incident
            return None
    
    async def run(self):
        self.running = True
        while self.running:
            try:
                await self.generate_incident()
                
                for patch in self.patches:
                    if patch['status'] in ['pending', 'in_progress']:
                        await self.progress_patch(patch)
                
                pending_count = len([p for p in self.patches if p['status'] in ['pending', 'in_progress']])
                self.metrics_cache["patchesPending"] = pending_count
                
                self.patches = [p for p in self.patches if p['status'] != 'completed' or 
                               (datetime.now() - p['created_at']).seconds < 300]
                
                await asyncio.sleep(random.randint(30, 60))
            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(5)
    
    def stop(self):
        self.running = False

live_generator = LiveDataGenerator()