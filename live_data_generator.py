import asyncio
import random
from datetime import datetime, timedelta
from data.alert_simulator import AlertSimulator
from data.metrics_simulator import MetricsSimulator
from agents.orchestrator import enhanced_orchestrator
from config.knowledge_base import kb
from config.action_executor import executor
from config.terminal_logger import terminal_logger

class LiveDataGenerator:
    # ===== CONFIGURATION CONSTANTS =====
    # PHASE 5: Patch management configuration (tunable parameters)
    PATCH_GENERATION_PROBABILITY = 0.50  # Probability to generate patch plan (50%)
    PATCH_RETENTION_SECONDS = 600        # Keep completed patches for 10 minutes
    PATCH_PHASE_DURATION = 20            # Seconds per patch phase (canary, phase2, phase3)
    PATCH_FAILURE_RATE = 0.98            # Probability patch succeeds (0.98 = 2% failure)

    # Action execution configuration
    ACTION_EXECUTION_PROBABILITY = 0.20  # Probability to execute action (80% = > 0.2)

    def __init__(self):
        self.alert_sim = AlertSimulator()
        self.metrics_sim = MetricsSimulator()
        self.running = False
        self.kill_switch_active = False
        self.simulation_running = False  # Controls incident generation (Start/Stop button)
        self.patches = []
        self.patch_counter = 0

        # Log buffer for terminal viewer
        self.log_buffer = []
        self.max_log_entries = 200
        
        # FIX: Initialize base metrics that persist
        # Start with baseline from manual operations before AI
        self.base_metrics = {
            "alertsReduced": 10.0,      # 10% baseline from manual correlation
            "mttrReduction": 5.0,       # 5% baseline from existing runbooks
            "tasksAutomated": 0,        # Start automating from scratch
        }
        
        # FIX: Separate dynamic metrics that change
        self.dynamic_metrics = {
            "activeIncidents": 0,
            "patchesPending": 0,
            "upcomingRisks": 5
        }
        
        # FIX: Combined metrics cache with proper initialization
        self.metrics_cache = {**self.base_metrics, **self.dynamic_metrics}
        
        self.recent_actions = []
        self.incident_times = {}
        
        # FIX: Add metrics lock for thread-safe updates
        self.metrics_lock = asyncio.Lock()
        self.generation_lock = asyncio.Lock()
        
        # FIX: Track incidents in processing to prevent state loss
        self.processing_incidents = set()

        # PHASE 5: Forecasting data cache
        self.forecast_cache = {
            "metrics": self._generate_initial_forecast(),
            "anomaly_detection_accuracy": 92.0,
            "risk_prediction_confidence": 87.0,
            "patch_success_rate": 94.0,
            "upcoming_risks": self._generate_upcoming_risks()
        }
    
    def toggle_kill_switch(self):
        """Toggle kill switch and log the state change"""
        self.kill_switch_active = not self.kill_switch_active

        if self.kill_switch_active:
            print("KILL SWITCH ACTIVATED - All autonomous actions paused")
            print("   - Incident generation: PAUSED")
            print("   - Action execution: BLOCKED")
            print("   - Patch deployments: PAUSED")
        else:
            print("KILL SWITCH DEACTIVATED - Autonomous actions resumed")
            print("   - Incident generation: ACTIVE")
            print("   - Action execution: ENABLED")
            print("   - Patch deployments: ACTIVE")

        status = "ACTIVE" if self.kill_switch_active else "INACTIVE"
        terminal_logger.add_log(f"Kill switch {status.lower()}", "KILLSWITCH")
        return self.kill_switch_active

    def get_kill_switch_state(self):
        """Get current kill switch state"""
        return self.kill_switch_active

    def start_simulation(self):
        """Start incident generation simulation"""
        if not self.simulation_running:
            self.simulation_running = True
            msg = "Incident simulation started - generating incidents every 30-60s"
            print(f"START: {msg}")
            terminal_logger.add_log(msg, "START")
            return True
        return False

    def stop_simulation(self):
        """Stop incident generation simulation"""
        if self.simulation_running:
            self.simulation_running = False
            msg = "Incident simulation stopped - no new incidents will be generated"
            print(f"STOP: {msg}")
            terminal_logger.add_log(msg, "STOP")
            terminal_logger.add_log(f"Total incidents generated this session: {len(kb.incident_memory)}", "INFO")
            return True
        return False

    def get_simulation_state(self):
        """Get current simulation running state"""
        return self.simulation_running

    # Removed add_log and get_logs methods - now using shared terminal_logger

    def _get_relative_time(self, timestamp):
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except ValueError:
                return timestamp

        delta = datetime.now() - timestamp
        total_seconds = delta.total_seconds()

        if total_seconds < 60:
            return "Just now"
        elif total_seconds < 3600:
            mins = int(total_seconds // 60)
            return f"{mins} min ago"
        elif total_seconds < 86400:
            hours = int(total_seconds // 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            days = int(total_seconds // 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"
    

    def _generate_initial_forecast(self):
        """PHASE 5: Generate initial 24-hour forecast data"""
        hours = list(range(24))
        cpu_actual = [40 + 15 * (i % 3) / 3 + random.uniform(-5, 5) for i in hours]
        cpu_predicted = [40 + 15 * (i % 3) / 3 for i in hours]
        memory_actual = [55 + 10 * ((i + 1) % 4) / 4 + random.uniform(-4, 4) for i in hours]

        return {
            "hours": [f"{h:02d}:00" for h in hours],
            "cpu": {
                "actual": cpu_actual,
                "predicted": cpu_predicted
            },
            "memory": {
                "actual": memory_actual,
                "threshold": 80.0
            }
        }

    def _generate_upcoming_risks(self):
        """PHASE 5: Generate upcoming risks with confidence scores"""
        now = datetime.now()
        risks = []

        # Risk 1: High CPU
        risk1_time = now + timedelta(hours=random.randint(2, 8))
        risks.append({
            "title": "CPU spike predicted on db-prod-01",
            "severity": "high",
            "expected_time": risk1_time.isoformat(),
            "expected_time_text": f"{risk1_time.strftime('%b %d, %I:%M %p')}",
            "confidence": 87 + random.uniform(-5, 5)
        })

        # Risk 2: Memory pressure
        risk2_time = now + timedelta(hours=random.randint(6, 24))
        risks.append({
            "title": "Memory exhaustion on web cluster",
            "severity": "medium",
            "expected_time": risk2_time.isoformat(),
            "expected_time_text": f"{risk2_time.strftime('%b %d, %I:%M %p')}",
            "confidence": 75 + random.uniform(-5, 5)
        })

        # Risk 3: Disk usage
        risk3_time = now + timedelta(hours=random.randint(12, 48))
        risks.append({
            "title": "Disk capacity warning on storage-01",
            "severity": "medium",
            "expected_time": risk3_time.isoformat(),
            "expected_time_text": f"{risk3_time.strftime('%b %d, %I:%M %p')}",
            "confidence": 68 + random.uniform(-5, 5)
        })

        # Risk 4: Network latency
        risk4_time = now + timedelta(hours=random.randint(8, 20))
        risks.append({
            "title": "Network latency spike predicted",
            "severity": "low",
            "expected_time": risk4_time.isoformat(),
            "expected_time_text": f"{risk4_time.strftime('%b %d, %I:%M %p')}",
            "confidence": 72 + random.uniform(-5, 5)
        })

        return risks

    def should_generate_patch(self, incident):
        """Generate patches for ~40% of resolved incidents"""
        # Generate patches when PatchOps is involved OR randomly for other incidents
        agents_involved = incident.get('agents_involved', [])
        if "PatchOps" in agents_involved:
            return True
        # Also generate patches for 40% of other resolved incidents
        return random.random() < 0.4
    
    def generate_patch_from_incident(self, incident):
        alerts = incident.get('alerts', [])
        component = "system"
        
        if alerts:
            if isinstance(alerts[0], dict):
                alert_title = alerts[0].get('title', '')
            else:
                alert_title = str(alerts[0])
            
            if "database" in alert_title.lower():
                component = "database"
            elif "web" in alert_title.lower() or "nginx" in alert_title.lower():
                component = "web-server"
            elif "memory" in alert_title.lower():
                component = "memory-mgmt"
            elif "cpu" in alert_title.lower():
                component = "compute"
            else:
                component = "system"
        
        self.patch_counter += 1
        return {
            "id": f"PLAN-{self.patch_counter:03d}",
            "name": f"openssl-{component} v1.{random.randint(1,9)}.{random.randint(0,20)}",
            "systems": random.randint(10, 50),
            "progress": 0,
            "status": "pending",
            "created_at": datetime.now(),
            "phases": [
                {"name": "Canary (5 hosts)", "status": "pending", "progress": 0},
                {"name": "Phase 2 (15 hosts)", "status": "pending", "progress": 0},
                {"name": "Phase 3 (remaining)", "status": "pending", "progress": 0}
            ],
            "risk_score": random.uniform(0.1, 0.4)
        }
    
    async def progress_patch(self, patch):
        if self.kill_switch_active and patch['status'] != 'paused':
            print(f"Kill switch active - Pausing patch {patch['id']}")
            patch['status'] = 'paused'
            return
        elif not self.kill_switch_active and patch['status'] == 'paused':
            print(f"Kill switch deactivated - Resuming patch {patch['id']}")
            patch['status'] = 'in_progress'
        
        if patch['status'] == 'pending':
            patch['status'] = 'in_progress'
            patch['phases'][0]['status'] = 'in_progress'
            
        if patch['status'] == 'in_progress':
            for i, phase in enumerate(patch['phases']):
                if phase['status'] == 'in_progress':
                    phase['progress'] += random.randint(15, 35)
                    
                    if phase['progress'] >= 100:
                        phase['progress'] = 100
                        
                        if random.random() > self.PATCH_FAILURE_RATE:
                            phase['status'] = 'failed'
                            patch['status'] = 'failed'
                            patch['progress'] = int((i * 100 + 100) / 3)
                            return
                        
                        phase['status'] = 'completed'
                        
                        if i < len(patch['phases']) - 1:
                            patch['phases'][i+1]['status'] = 'in_progress'
                        else:
                            patch['status'] = 'completed'
                    
                    patch['progress'] = int(sum(p['progress'] for p in patch['phases']) / len(patch['phases']))
                    break

    # FIX: New method for atomic metric updates
    async def update_metrics_atomically(self, updates: dict):
        """Atomically update metrics to prevent state loss"""
        async with self.metrics_lock:
            # Update base metrics incrementally
            for key in ["alertsReduced", "mttrReduction", "tasksAutomated"]:
                if key in updates:
                    self.base_metrics[key] = updates[key]
            
            # Update dynamic metrics
            for key in ["activeIncidents", "patchesPending", "upcomingRisks"]:
                if key in updates:
                    self.dynamic_metrics[key] = updates[key]
            
            # Rebuild cache from both sources
            self.metrics_cache = {**self.base_metrics, **self.dynamic_metrics}
    
    # FIX: New method to calculate active incidents safely
    async def calculate_active_incidents(self):
        """Calculate active incidents including those being processed"""
        async with self.metrics_lock:
            # Count pending incidents in KB
            pending_in_kb = len([i for i in kb.incident_memory.values() 
                               if i.get('outcome') == 'pending'])
            
            # Add incidents currently being processed
            total_active = pending_in_kb + len(self.processing_incidents)
            
            return total_active
    
    async def generate_incident(self):
        try:
            if self.kill_switch_active:
                print("Kill switch active - Skipping incident generation")
                return None

            # Get all available patterns from alert simulator
            patterns = list(self.alert_sim.ALERT_PATTERNS.keys())
            pattern = random.choice(patterns)

            # NARRATIVE: Pattern selection
            terminal_logger.add_log(f"Selected incident pattern: {pattern}", "GENERATOR")

            alerts = self.alert_sim.generate_alert_cluster(pattern)

            # NARRATIVE: Alert generation
            alert_titles = [a.title for a in alerts[:3]]  # First 3 alert titles
            terminal_logger.add_log(f"Generating alert cluster: {len(alerts)} alerts ({', '.join(alert_titles)}...)", "GENERATOR")

            metrics = self.metrics_sim.generate_failure_pattern(
                f"host-{random.randint(1,10)}",
                random.choice(["cpu_spike", "memory_leak"])
            )

            # NARRATIVE: Metrics generation
            terminal_logger.add_log(f"Generating metrics: {len(metrics)} data points for failure pattern analysis", "GENERATOR")

            # Store placeholder incident IMMEDIATELY so frontend can see it
            import uuid
            incident_id = f"INC-{uuid.uuid4().hex[:8]}"
            self.incident_times[incident_id] = datetime.now()
            
            # FIX: Add to processing set BEFORE creating placeholder
            self.processing_incidents.add(incident_id)

            # Prepare alert details for placeholder
            alert_details = [
                {
                    "alert_id": a.alert_id,
                    "title": a.title,
                    "description": a.description,
                    "severity": a.severity.value,
                    "host": a.host,
                    "timestamp": a.timestamp.isoformat(),
                    "source": a.source,
                    "tags": a.tags
                }
                for a in alerts
            ]

            # Create placeholder in knowledge base
            # FIX: Don't set agents_involved until orchestrator completes analysis
            # This prevents API from showing incomplete agent list during brief initial period
            creation_time = datetime.now()
            kb.store_incident({
                "incident_id": incident_id,
                "alerts": alert_details,
                "alert_ids": [a.alert_id for a in alerts],
                "root_cause": "Processing...",
                "agents_involved": [],  # Will be set by Orchestrator after agent selection
                "outcome": "pending",
                "metadata": {"status": "processing"},
                "processing_state": "created",
                "created_at": creation_time
            })

            print(f"Created placeholder incident {incident_id} (Total incidents: {len(kb.incident_memory)})")

            # NARRATIVE: Incident created
            primary_alert = alerts[0] if alerts else None
            if primary_alert:
                terminal_logger.add_log(
                    f"Incident {incident_id} created: {primary_alert.title} on {primary_alert.host}",
                    "INCIDENT"
                )
            else:
                terminal_logger.add_log(f"Incident {incident_id} created", "INCIDENT")

            # FIX: Update metrics incrementally without overwriting
            active_count = await self.calculate_active_incidents()
            
            # Increment base metrics gradually with realistic improvements per incident
            # Each incident reduces 2-8% of alerts in its cluster (much more believable)
            new_alerts_reduced = min(85, self.base_metrics["alertsReduced"] + random.uniform(2.0, 8.0))
            # Each successful automation saves 1.5-4% MTTR improvement
            new_mttr_reduction = min(50, self.base_metrics["mttrReduction"] + random.uniform(1.5, 4.0))
            # Each incident automates 1-3 tasks
            new_tasks_automated = self.base_metrics["tasksAutomated"] + random.randint(1, 3)

            # FIX: Update all metrics atomically to prevent race condition
            # Don't update base_metrics directly - use atomic method only
            await self.update_metrics_atomically({
                "activeIncidents": active_count,
                "alertsReduced": new_alerts_reduced,
                "mttrReduction": new_mttr_reduction,
                "tasksAutomated": new_tasks_automated
            })

            # Update forecast data without resetting
            self.forecast_cache["anomaly_detection_accuracy"] = min(98, self.forecast_cache["anomaly_detection_accuracy"] + random.uniform(0, 0.5))
            self.forecast_cache["risk_prediction_confidence"] = min(95, self.forecast_cache["risk_prediction_confidence"] + random.uniform(0, 0.5))
            self.forecast_cache["patch_success_rate"] = min(99, self.forecast_cache["patch_success_rate"] + random.uniform(0, 0.2))
            
            # Only regenerate risks occasionally, not every time
            if random.random() < 0.3:  # 30% chance
                self.forecast_cache["upcoming_risks"] = self._generate_upcoming_risks()

            print(f"Metrics updated incrementally - activeIncidents: {active_count}")

            # NARRATIVE: Metrics update
            terminal_logger.add_log(
                f"System metrics updated - Active incidents: {active_count}, Alerts reduced: {new_alerts_reduced:.1f}%",
                "METRICS"
            )

            # Now do the actual processing (this takes time)
            async with self.generation_lock:
                try:
                    # Update incident state to analyzing
                    incident = kb.get_incident(incident_id)
                    if incident:
                        incident['processing_state'] = 'analyzing'
                        kb.incident_memory[incident_id] = incident

                    # NARRATIVE: Starting orchestration
                    terminal_logger.add_log(
                        f"Orchestrator initiating analysis pipeline for {incident_id}",
                        "ORCHESTRATOR"
                    )

                    # Run heavy processing off the event loop to keep API responsive
                    # Orchestrator will decide which agents to invoke based on incident content
                    result = await asyncio.to_thread(
                        enhanced_orchestrator.handle_incident_full,
                        alerts,
                        metrics,
                        incident_id=incident_id
                    )

                    print(f"Completed processing {incident_id} (Total incidents: {len(kb.incident_memory)})")

                    # NARRATIVE: Analysis complete
                    terminal_logger.add_log(f"Analysis pipeline completed for {incident_id}", "ORCHESTRATOR")

                    # Get agents that were actually involved from the incident record
                    incident_record = kb.get_incident(incident_id)
                    agents_used = incident_record.get('agents_involved', ['Orchestrator']) if incident_record else ['Orchestrator']

                    # Record agent analysis actions (so agents show activity in dashboard)
                    analysis_time = datetime.now()
                    for agent in agents_used:
                        # Add to incident actions
                        kb.add_incident_action(incident_id, {
                            'type': 'analyze_incident',
                            'action_type': 'analyze_incident',
                            'agent': agent,
                            'description': f"Agent {agent} analyzed incident and provided insights",
                            'status': 'completed',
                            'timestamp': analysis_time
                        })

                        # Add to recent actions for dashboard display
                        self.recent_actions.insert(0, {
                            "agent": agent,
                            "action": "Analyzed incident",
                            "timestamp": analysis_time,
                            "relative_time": self._get_relative_time(analysis_time)
                        })

                    # Trim recent actions to prevent memory bloat
                    if len(self.recent_actions) > 50:
                        self.recent_actions = self.recent_actions[:50]

                    # Generate patch with the actual incident record
                    incident_record = kb.get_incident(incident_id)
                    if incident_record:
                        # Update state to resolved and add timestamp
                        incident_record['processing_state'] = 'resolved'
                        incident_record['resolved_at'] = datetime.now()
                        kb.incident_memory[incident_id] = incident_record

                        # FIX: Remove from processing_incidents to prevent memory leak
                        self.processing_incidents.discard(incident_id)

                        if self.should_generate_patch(incident_record):
                            new_patch = self.generate_patch_from_incident(incident_record)
                            new_patch['incident_id'] = incident_id
                            self.patches.append(new_patch)
                            print(f"📦 Generated patch: {new_patch['name']}")

                            # NARRATIVE: Patch generation
                            terminal_logger.add_log(
                                f"PatchOps generated preventative patch: {new_patch['name']}",
                                "PATCHOPS"
                            )

                    # Execute actions if needed
                    if self.kill_switch_active:
                        print("Kill switch active - Blocking action execution")
                        terminal_logger.add_log("Kill switch active - Action execution blocked", "WARNING")
                    elif random.random() > self.ACTION_EXECUTION_PROBABILITY:
                        action_time = datetime.now()
                        executed_actions = []

                        for agent in agents_used:
                            action = {
                                "type": random.choice(["suppress_alerts", "restart_service", "clear_cache"]),
                                "params": {"host": f"host-{random.randint(1, 10)}"},
                                "risk_level": "LOW",
                                "agent": agent
                            }

                            exec_result = executor.execute_action(action, incident_id=incident_id)
                            executed_actions.append(f"{agent}: {action['type']}")

                            kb.add_incident_action(incident_id, {
                                'type': action['type'],
                                'action_type': action['type'],
                                'agent': agent,
                                'description': f"Agent {agent} executed {action['type']}",
                                'status': 'completed',
                                'timestamp': action_time
                            })

                            self.recent_actions.insert(0, {
                                "agent": agent,
                                "action": f"Executed {action['type']}",
                                "timestamp": action_time,
                                "relative_time": self._get_relative_time(action_time)
                            })

                        if len(self.recent_actions) > 50:
                            self.recent_actions = self.recent_actions[:50]

                        # NARRATIVE: Actions executed
                        for action_desc in executed_actions:
                            terminal_logger.add_log(f"Executed action: {action_desc}", "TASKOPTS")
                        terminal_logger.add_log(
                            f"TaskOps completed {len(executed_actions)} remediation actions for {incident_id}",
                            "SUCCESS"
                        )
                    
                finally:
                    # FIX: Remove from processing set when done
                    self.processing_incidents.discard(incident_id)

            # FIX: Final metric update with accurate count
            final_active_count = await self.calculate_active_incidents()
            await self.update_metrics_atomically({
                "activeIncidents": final_active_count
            })
            
            print(f"Final metrics update - activeIncidents: {final_active_count}")

            return result

        except Exception as e:
            print(f"Error generating incident: {e}")
            import traceback
            traceback.print_exc()
            
            # FIX: Clean up processing set on error
            if incident_id:
                self.processing_incidents.discard(incident_id)
                
                # Mark incident as failed
                if incident_id in kb.incident_memory:
                    incident = kb.get_incident(incident_id)
                    if incident and incident.get('root_cause') == "Processing...":
                        incident['root_cause'] = f"Error: {str(e)[:100]}"
                        incident['metadata'] = {"status": "failed"}
                        incident['processing_state'] = 'failed'
                        kb.incident_memory[incident_id] = incident
            
            # FIX: Update metrics even on error
            final_active_count = await self.calculate_active_incidents()
            await self.update_metrics_atomically({
                "activeIncidents": final_active_count
            })
            
            return None
    
    async def run(self):
        self.running = True
        while self.running:
            try:
                # Only generate incidents if simulation is running
                if self.simulation_running:
                    await self.generate_incident()

                    # Process patches
                    for patch in self.patches:
                        if patch['status'] in ['pending', 'in_progress']:
                            await self.progress_patch(patch)

                    # FIX: Update pending patches count atomically
                    pending_count = len([p for p in self.patches if p['status'] in ['pending', 'in_progress']])
                    await self.update_metrics_atomically({
                        "patchesPending": pending_count
                    })

                    # Clean up old completed patches
                    self.patches = [p for p in self.patches if p['status'] != 'completed' or
                                   (datetime.now() - p['created_at']).total_seconds() < self.PATCH_RETENTION_SECONDS]

                    await asyncio.sleep(random.randint(30, 60))
                else:
                    # Simulation paused - just wait briefly and check again
                    await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Error in run loop: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(5)
    
    def stop(self):
        self.running = False

# Create singleton instance
live_generator = LiveDataGenerator()
