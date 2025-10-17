from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from datetime import datetime, timedelta
from config.knowledge_base import kb
from config.action_executor import executor
from live_data_generator import live_generator

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(live_generator.run())

@app.on_event("shutdown")
async def shutdown_event():
    live_generator.stop()

@app.get("/api/metrics")
async def get_metrics():
    print(f"📊 API /metrics called - returning: {live_generator.metrics_cache}")
    return live_generator.metrics_cache

@app.get("/api/agents")
async def get_agents():
    print(f"📊 API /agents called - recent_actions: {len(live_generator.recent_actions)}, incidents: {len(kb.incident_memory)}")

    agents = []
    agent_names = ['AlertOps', 'PredictiveOps', 'PatchOps', 'TaskOps', 'Orchestrator']

    for agent_name in agent_names:
        try:
            action_count = len([a for a in live_generator.recent_actions if a.get('agent') == agent_name])
            recent_action = next((a for a in live_generator.recent_actions if a.get('agent') == agent_name), None)

            agents.append({
                "name": agent_name,
                "status": "active",
                "actions": max(action_count, len(kb.incident_memory) if agent_name == 'Orchestrator' else 0),
                "lastAction": recent_action.get('relative_time') if recent_action else "N/A",
                "lastActionTime": recent_action.get('timestamp').isoformat() if recent_action and recent_action.get('timestamp') else None
            })
        except Exception as e:
            print(f"⚠️ Error processing agent {agent_name}: {e}")
            # Add agent with default values to prevent empty response
            agents.append({
                "name": agent_name,
                "status": "active",
                "actions": 0,
                "lastAction": "N/A",
                "lastActionTime": None
            })

    print(f"📊 API /agents returning {len(agents)} agents")
    return agents


@app.get("/api/incidents")
async def get_incidents():
    # DEBUG: Log the state of incident_memory
    print(f"📊 API /incidents called - KB has {len(kb.incident_memory)} incidents: {list(kb.incident_memory.keys())}")

    incidents = []
    incident_items = list(kb.incident_memory.items())

    for inc_id, inc in incident_items[-20:]:
        try:
            print(f"  Processing incident {inc_id}: root_cause={inc.get('root_cause', 'N/A')[:50]}, alerts count={len(inc.get('alerts', []))}")
            created_time = live_generator.incident_times.get(inc_id, datetime.now())

            # Get alerts FIRST (needed for severity calculation)
            alerts = inc.get('alerts', [])

            # Handle processing incidents
            root_cause = inc.get('root_cause', '')
            if root_cause == "Processing...":
                title = "Incident processing..."
            else:
                title = "System incident"
                if alerts and len(alerts) > 0:
                    alert_str = str(alerts[0])
                    if "title='" in alert_str:
                        title = alert_str.split("title='")[1].split("'")[0]
                    elif 'title="' in alert_str:
                        title = alert_str.split('title="')[1].split('"')[0]

            age_minutes = (datetime.now() - created_time).seconds // 60
            if age_minutes > 10:
                status = "resolved"
            elif age_minutes > 5:
                status = "in_progress"
            else:
                status = "investigating"

            incidents.append({
                "id": inc_id,
                "title": title,
                "severity": "critical" if len(alerts) > 5 else "high",
                "status": status,
                "time": created_time.isoformat(),
                "relative_time": live_generator._get_relative_time(created_time),
                "agents": inc.get('agents_involved', [])
            })
        except Exception as e:
            # Log error but continue processing other incidents
            print(f"⚠️ Error processing incident {inc_id}: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"📊 API /incidents returning {len(incidents)} incidents")
    return incidents[::-1]
@app.get("/api/incidents/{incident_id}")
async def get_incident_detail(incident_id: str):
    incident = kb.get_incident(incident_id)
    if not incident:
        return {"error": "Not found"}
    
    # Get actual incident time
    created_time = live_generator.incident_times.get(incident_id, datetime.now())
    
    # Extract real root cause from synthesis or alerts
    root_cause = "Unknown"
    if incident.get('root_cause'):
        root_cause = incident['root_cause']
    elif incident.get('alerts'):
        first_alert = str(incident['alerts'][0])
        if "title='" in first_alert:
            root_cause = first_alert.split("title='")[1].split("'")[0]
    
    # Build real timeline from incident data
    timeline = []
    timeline.append({
        "time": created_time.strftime("%H:%M"),
        "event": "Initial alert received"
    })
    
    if incident.get('agents_involved'):
        for i, agent in enumerate(incident['agents_involved'][:3], 1):
            event_time = created_time + timedelta(minutes=i)
            timeline.append({
                "time": event_time.strftime("%H:%M"),
                "event": f"{agent} processed incident"
            })
    
    # Add actions from recent_actions
    for action in live_generator.recent_actions:
        if hasattr(action.get('timestamp'), 'strftime'):
            timeline.append({
                "time": action['timestamp'].strftime("%H:%M"),
                "event": f"Action executed: {action['action']}"
            })
            if len(timeline) >= 6:
                break
    
    return {
        "id": incident_id,
        "details": incident,
        "why_trace": f"Root cause: {root_cause}",
        "timeline": timeline
    }

@app.get("/api/actions/recent")
async def get_recent_actions():
    actions = []
    for action in live_generator.recent_actions[:10]:
        try:
            actions.append({
                "agent": action.get('agent', 'Unknown'),
                "action": action.get('action', 'Unknown action'),
                "time": live_generator._get_relative_time(action.get('timestamp', datetime.now()))
            })
        except Exception as e:
            print(f"⚠️ Error processing action: {e}")
            continue
    return actions

@app.get("/api/patches")
async def get_patches():
    return [
        {
            "id": p['id'],
            "name": p['name'],
            "systems": p['systems'],
            "progress": p['progress'],
            "status": p['status']
        }
        for p in live_generator.patches
    ]

@app.get("/api/patches/{plan_id}")
async def get_patch_detail(plan_id: str):
    patch = next((p for p in live_generator.patches if p['id'] == plan_id), None)
    if not patch:
        return {"error": "Not found"}
    
    return {
        "id": patch['id'],
        "name": patch['name'],
        "canary_phases": patch.get('phases', []),
        "affected_hosts": [f"host-{i}" for i in range(1, min(6, patch['systems']))],
        "rollback_plan": "Automated rollback within 10 minutes if health checks fail",
        "health_checks": ["CPU < 80%", "Memory < 70%", "Service response < 200ms"]
    }

@app.get("/api/audit-logs")
async def get_audit_logs():
    logs = []
    for i, log_entry in enumerate(executor.execution_log[-50:]):
        logs.append({
            "id": log_entry.get("action_id", f"ACT-{i:03d}"),
            "agent": "PatchOps",
            "action": log_entry.get("type", "Unknown"),
            "target": log_entry.get("params", {}).get("host", "N/A"),
            "status": log_entry.get("status", "unknown"),
            "time": log_entry.get("timestamp", "N/A")
        })
    return logs[::-1]

@app.post("/api/kill-switch/toggle")
async def toggle_kill_switch():
    state = live_generator.toggle_kill_switch()
    return {
        "active": state,
        "message": "Kill switch activated - all autonomous actions paused" if state else "Kill switch deactivated - autonomous actions resumed"
    }

@app.get("/api/kill-switch/status")
async def get_kill_switch_status():
    return {"active": live_generator.get_kill_switch_state()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)