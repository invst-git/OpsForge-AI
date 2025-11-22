from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from config.knowledge_base import kb
from config.action_executor import executor
from config.text_formatter import (
    format_incident_title,
    format_root_cause_analysis,
    humanize_action_type,
    humanize_status,
    format_timeline_event,
    format_llm_synthesis,
    format_datetime
)
from live_data_generator import live_generator

# Modern lifespan context manager (replaces deprecated @app.on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the live data generator
    asyncio.create_task(live_generator.run())
    yield
    # Shutdown: Stop the live data generator
    live_generator.stop()

app = FastAPI(lifespan=lifespan)

# Get CORS origin from environment variable, fallback to localhost for development
cors_origin = os.getenv("CORS_ORIGIN", "http://localhost:5173")
# Support multiple origins if comma-separated
cors_origins = [origin.strip() for origin in cors_origin.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FIX: Add state tracking to prevent concurrent issues
api_state = {
    "last_metrics_snapshot": None,
    "metrics_update_lock": asyncio.Lock()
}

@app.get("/api/metrics")
async def get_metrics():
    """FIX: Return consistent metrics snapshot"""
    try:
        # Use the lock to ensure we get a consistent snapshot
        async with api_state["metrics_update_lock"]:
            # Return a copy to prevent external modification
            metrics_snapshot = dict(live_generator.metrics_cache)
            api_state["last_metrics_snapshot"] = metrics_snapshot
        print(f"[API] /metrics called - returning: {metrics_snapshot}")
        return metrics_snapshot
    except Exception as e:
        print(f"[ERROR] Failed to fetch metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {str(e)}")

@app.get("/api/agents")
async def get_agents():
    """FIX: Improved agent stats with proper action counting"""
    try:
        print(f"[API] /agents called - recent_actions: {len(live_generator.recent_actions)}, incidents: {len(kb.incident_memory)}")

        agents = []
        agent_names = ['AlertOps', 'PredictiveOps', 'PatchOps', 'TaskOps', 'Orchestrator']

        for agent_name in agent_names:
            try:
                # FIX: Count from incident_actions only (single authoritative source)
                # This prevents double-counting actions that appear in both recent_actions and incident_actions
                incident_action_count = 0
                latest_incident_action_time = None
                latest_incident_action = None

                for incident in kb.incident_memory.values():
                    incident_actions = incident.get('incident_actions', [])
                    for action in incident_actions:
                        if action.get('agent') == agent_name:
                            incident_action_count += 1
                            action_timestamp = action.get('timestamp')
                            if action_timestamp:
                                if latest_incident_action_time is None or action_timestamp > latest_incident_action_time:
                                    latest_incident_action_time = action_timestamp
                                    latest_incident_action = action

                # Use incident_actions as the single source of truth
                total_action_count = incident_action_count

                # Get last action time from incident_actions
                last_action_time = latest_incident_action_time

                # Format last action time
                last_action_str = "N/A"
                last_action_iso = None
                if last_action_time:
                    try:
                        # Normalize integer timestamps from KnowledgeBase to datetime
                        if isinstance(last_action_time, (int, float)):
                            from datetime import datetime as dt
                            last_action_time = dt.fromtimestamp(last_action_time)

                        last_action_str = live_generator._get_relative_time(last_action_time)
                        if isinstance(last_action_time, str):
                            last_action_iso = last_action_time
                        else:
                            last_action_iso = last_action_time.isoformat()
                    except:
                        last_action_str = "N/A"

                agents.append({
                    "name": agent_name,
                    "status": "active",
                    "actions": total_action_count,
                    "lastAction": last_action_str,
                    "lastActionTime": last_action_iso
                })

            except Exception as e:
                print(f"[ERROR] Error processing agent {agent_name}: {e}")
                import traceback
                traceback.print_exc()
                # Add agent with default values to prevent empty response
                agents.append({
                    "name": agent_name,
                    "status": "active",
                    "actions": 0,
                    "lastAction": "N/A",
                    "lastActionTime": None
                })

        print(f"[API] /agents returning {len(agents)} agents")
        return agents
    except Exception as e:
        print(f"[ERROR] Failed to fetch agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch agents: {str(e)}")


@app.get("/api/incidents")
async def get_incidents():
    """FIX: Return incidents with proper state handling"""
    try:
        print(f"[API] /incidents called - KB has {len(kb.incident_memory)} incidents: {list(kb.incident_memory.keys())}")

        incidents = []
        incident_items = list(kb.incident_memory.items())

        for inc_id, inc in incident_items[-20:]:
            try:
                print(f"  Processing incident {inc_id}: state={inc.get('processing_state', 'unknown')}, root_cause={inc.get('root_cause', 'N/A')[:50]}")

                created_time = live_generator.incident_times.get(inc_id, datetime.now())

                # Get alerts (now stored as full details)
                alerts = inc.get('alerts', [])

                # Handle processing incidents with proper state
                root_cause = inc.get('root_cause', '')
                processing_state = inc.get('processing_state', 'created')

                # FIX: Better title handling based on processing state
                if processing_state in ['created', 'analyzing'] or root_cause == "Processing...":
                    title = "Incident Analysis In Progress"
                else:
                    # Extract title from first alert
                    if alerts and len(alerts) > 0:
                        if isinstance(alerts[0], dict):
                            title = format_incident_title(alerts[0].get('title', 'System Incident'))
                        else:
                            # Fallback for old format
                            alert_str = str(alerts[0])
                            if "title='" in alert_str:
                                raw_title = alert_str.split("title='")[1].split("'")[0]
                            elif 'title="' in alert_str:
                                raw_title = alert_str.split('title="')[1].split('"')[0]
                            else:
                                raw_title = "System Incident"
                            title = format_incident_title(raw_title)
                    else:
                        title = "System Incident"

                # FIX: Use processing_state for accurate status
                if processing_state == 'created':
                    status = "investigating"
                elif processing_state == 'analyzing':
                    status = "investigating"
                elif processing_state == 'remediation_in_progress':
                    status = "in_progress"
                elif processing_state == 'resolved':
                    status = "resolved"
                elif processing_state == 'failed':
                    status = "failed"
                else:
                    # Fallback: use time-based logic
                    age_seconds = (datetime.now() - created_time).total_seconds()
                    age_minutes = age_seconds / 60

                    if age_minutes > 10:
                        status = "resolved"
                    elif age_minutes > 5:
                        status = "in_progress"
                    else:
                        status = "investigating"

                # Format root cause for display
                if root_cause == "Processing...":
                    formatted_root_cause = "Analysis in progress..."
                elif root_cause.startswith("Error:"):
                    formatted_root_cause = root_cause
                else:
                    formatted_root_cause = format_root_cause_analysis(root_cause)

                # Count alerts properly
                alert_count = len(alerts)

                # Get severity with proper fallback
                severity = "medium"
                if alerts:
                    if isinstance(alerts[0], dict):
                        severity = alerts[0].get('severity', 'medium')
                    else:
                        alert_str = str(alerts[0])
                        if "severity='critical'" in alert_str or 'severity="critical"' in alert_str:
                            severity = "critical"
                        elif "severity='high'" in alert_str or 'severity="high"' in alert_str:
                            severity = "high"

                # Calculate time properly
                created_str = format_datetime(created_time)
                relative_time = live_generator._get_relative_time(created_time)

                incidents.append({
                    "id": inc_id,
                    "title": title,
                    "status": status,
                    "severity": severity,
                    "alerts": alert_count,
                    "time": relative_time,
                    "createdAt": created_time.isoformat(),
                    "rootCause": formatted_root_cause,
                    "agents": inc.get('agents_involved', []),
                    "processingState": processing_state  # FIX: Include processing state
                })

            except Exception as e:
                print(f"[ERROR] Error processing incident {inc_id}: {e}")
                import traceback
                traceback.print_exc()
                continue

        # FIX: Sort by creation time, newest first
        incidents.sort(key=lambda x: x['createdAt'], reverse=True)

        print(f"[API] /incidents returning {len(incidents)} incidents")
        return incidents
    except Exception as e:
        print(f"[ERROR] Failed to fetch incidents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch incidents: {str(e)}")

@app.get("/api/incidents/{incident_id}")
async def get_incident_detail(incident_id: str):
    """FIX: Get incident details with complete structure for CSV export"""
    incident = kb.get_incident(incident_id)
    if not incident:
        return {"error": "Incident not found"}

    # Get creation time from incident record or fallback to incident_times
    created_time = incident.get('created_at')
    if not created_time:
        created_time = live_generator.incident_times.get(incident_id, datetime.now())
    elif isinstance(created_time, str):
        from datetime import datetime as dt
        created_time = dt.fromisoformat(created_time)

    # Get alerts
    alerts = incident.get('alerts', [])

    # Extract title from first alert
    title = "System Incident"
    severity = "medium"
    if alerts and len(alerts) > 0:
        if isinstance(alerts[0], dict):
            title = format_incident_title(alerts[0].get('title', 'System Incident'))
            severity = alerts[0].get('severity', 'medium')
        else:
            # Fallback for old format
            alert_str = str(alerts[0])
            if "title='" in alert_str:
                raw_title = alert_str.split("title='")[1].split("'")[0]
                title = format_incident_title(raw_title)
            if "severity='critical'" in alert_str or 'severity="critical"' in alert_str:
                severity = "critical"
            elif "severity='high'" in alert_str or 'severity="high"' in alert_str:
                severity = "high"

    # Get processing state and derive status
    processing_state = incident.get('processing_state', 'created')
    if processing_state == 'created':
        status = "investigating"
    elif processing_state == 'analyzing':
        status = "investigating"
    elif processing_state == 'remediation_in_progress':
        status = "in_progress"
    elif processing_state == 'resolved':
        status = "resolved"
    elif processing_state == 'failed':
        status = "failed"
    else:
        status = "investigating"

    # Calculate timestamps
    created_at = created_time.isoformat()
    resolved_at = None
    resolved_time = None
    if status == "resolved" or processing_state == "resolved":
        # Prefer real resolved_at if available
        resolved_time = incident.get('resolved_at')

        # If not present, derive from timeline or incident actions
        if not resolved_time:
            try:
                timeline_events = incident.get('processing_timeline', [])
                candidate_ts = None
                # Use max timeline timestamp if available
                if timeline_events:
                    candidate_ts = max(
                        (e.get('timestamp') for e in timeline_events if e.get('timestamp') is not None),
                        default=None
                    )
                # Fallback to latest incident_action timestamp
                if candidate_ts is None:
                    incident_actions = incident.get('incident_actions', [])
                    candidate_ts = max(
                        (a.get('timestamp') for a in incident_actions if a.get('timestamp') is not None),
                        default=None
                    )
                if candidate_ts is not None:
                    from datetime import datetime as dt
                    # candidate_ts is stored as Unix epoch seconds (int)
                    resolved_time = dt.fromtimestamp(candidate_ts)
            except Exception:
                resolved_time = None

        if resolved_time:
            if isinstance(resolved_time, str):
                resolved_at = resolved_time
            else:
                resolved_at = resolved_time.isoformat()

    # Format root cause
    root_cause = incident.get('root_cause', 'Unknown')
    if root_cause == "Processing...":
        formatted_root_cause = "Analysis in progress..."
    else:
        formatted_root_cause = format_root_cause_analysis(root_cause)

    # Derive a concise root cause summary for exports
    if root_cause == "Processing...":
        root_cause_summary = "Analysis in progress..."
    else:
        # Use raw root_cause text to keep summary focused
        root_cause_summary = format_llm_synthesis(str(root_cause), max_length=200)

    # Derive affected components with sensible fallback
    affected_components = incident.get('affected_components')
    if not affected_components:
        # Fallback: use unique hosts from alerts as components
        hosts = set()
        for alert in alerts:
            if isinstance(alert, dict):
                host = alert.get('host')
                if host:
                    hosts.add(host)
        affected_components = sorted(hosts) if hosts else []

    # Derive correlation score / confidence if not already stored
    correlation_score = incident.get('correlation_score')
    confidence_score = incident.get('confidence')
    if correlation_score is None or confidence_score is None:
        try:
            from agents.strands_tools import correlate_alerts
            alert_dicts = []
            for alert in alerts:
                if isinstance(alert, dict):
                    alert_dicts.append({
                        "alert_id": alert.get("alert_id"),
                        "title": alert.get("title", ""),
                        "host": alert.get("host", ""),
                        "timestamp": alert.get("timestamp"),
                        "severity": alert.get("severity", "medium"),
                    })
            if alert_dicts:
                corr_result = correlate_alerts(alert_dicts)
                if correlation_score is None:
                    correlation_score = corr_result.get("confidence")
                if confidence_score is None:
                    confidence_score = corr_result.get("confidence")
        except Exception:
            pass

    # Format why-trace analysis
    formatted_why_trace = {
        "analysis": formatted_root_cause,
        "affected_components": affected_components,
        "correlation_score": correlation_score,
        "confidence": confidence_score,
        "recommended_actions": [
            format_llm_synthesis(action)
            for action in incident.get('recommended_actions', [])
        ]
    }

    # Build timeline with proper formatting
    timeline = []
    
    # Add alert timeline events
    alerts = incident.get('alerts', [])
    for alert in alerts:
        if isinstance(alert, dict):
            alert_timestamp = alert.get('timestamp', 'N/A')
            formatted_alert_time = format_datetime(alert_timestamp, 'short') if alert_timestamp != 'N/A' else 'N/A'
            timeline.append({
                "time": formatted_alert_time,
                "event": format_timeline_event(f"Alert: {alert.get('title', 'Unknown')}")
            })

    # Add action timeline events
    incident_actions = incident.get('incident_actions', [])
    for action in incident_actions:
        action_timestamp = action.get('timestamp')
        if action_timestamp:
            formatted_time = "N/A"
            try:
                if isinstance(action_timestamp, int):
                    from datetime import datetime as dt
                    dt_obj = dt.fromtimestamp(action_timestamp)
                    formatted_time = format_datetime(dt_obj, 'short')
                else:
                    formatted_time = format_datetime(action_timestamp, 'short')
            except:
                formatted_time = str(action_timestamp)

            timeline.append({
                "time": formatted_time,
                "event": format_timeline_event(f"{action.get('agent', 'Unknown')} {action.get('action_type', action.get('type', 'action'))}")
            })

    # Sort timeline by time
    timeline.sort(key=lambda x: x['time'])

    # Build audit logs
    audit_logs = []
    for i, action in enumerate(incident_actions):
        # FIX: Use 'action_type' field with proper fallback
        action_type = action.get('action_type', action.get('type', 'Unknown'))
        formatted_action = humanize_action_type(action_type)

        status = action.get('status', 'unknown')
        formatted_status = humanize_status(status)

        # Format timestamp
        action_timestamp = action.get('timestamp')
        formatted_time = "N/A"
        if action_timestamp:
            try:
                if isinstance(action_timestamp, int):
                    from datetime import datetime as dt
                    dt_obj = dt.fromtimestamp(action_timestamp)
                    formatted_time = format_datetime(dt_obj, 'full')
                else:
                    formatted_time = format_datetime(action_timestamp, 'full')
            except:
                formatted_time = str(action_timestamp)

        audit_logs.append({
            "id": action.get('action_id', f"ACT-{i:03d}"),
            "agent": action.get('agent', 'Unknown'),
            "action": formatted_action,
            "status": formatted_status.lower(),
            "time": formatted_time,
            "description": action.get('description', 'No description')
        })

    # Return comprehensive structure for CSV export and detail view
    return {
        "id": incident_id,
        "title": title,
        "severity": severity,
        "status": status,
        "created_at": created_at,
        "createdAt": created_at,  # Support both snake_case and camelCase
        "resolved_at": resolved_at,
        "resolvedAt": resolved_at,
        "alerts": alerts,  # Full alert array for CSV export
        "agents_involved": incident.get('agents_involved', []),
        "processing_state": processing_state,
        "processingState": processing_state,
        "why_trace": formatted_why_trace,
        "root_cause_summary": root_cause_summary,
        "rootCauseSummary": root_cause_summary,
        "rootCause": formatted_root_cause,  # For backward compatibility
        "timeline": timeline,
        "audit_logs": audit_logs,
        # Keep original incident data for any other needs
        "details": incident
    }

@app.get("/api/actions/recent")
async def get_recent_actions():
    """Get recent actions with proper formatting"""
    actions = []
    for action in live_generator.recent_actions[:10]:
        try:
            # Format the action text
            action_text = action.get('action', 'Unknown action')
            if 'Executed ' in action_text:
                # Extract action type and humanize it
                action_type = action_text.replace('Executed ', '')
                action_text = humanize_action_type(action_type)

            actions.append({
                "agent": action.get('agent', 'Unknown'),
                "action": action_text,
                "time": live_generator._get_relative_time(action.get('timestamp', datetime.now()))
            })
        except Exception as e:
            print(f"[ERROR] Error processing action: {e}")
            continue
    return actions

@app.get("/api/patches")
async def get_patches():
    """Get patch information"""
    return [
        {
            "id": p['id'],
            "name": p['name'],
            "systems": p['systems'],
            "progress": p['progress'],
            "status": p['status'],
            # Non-breaking additional context for richer UI
            "created_at": (
                p.get("created_at").isoformat()
                if isinstance(p.get("created_at"), datetime)
                else p.get("created_at")
            ),
            "risk_score": p.get("risk_score"),
            "incident_id": p.get("incident_id"),
        }
        for p in live_generator.patches
    ]

@app.get("/api/patches/{plan_id}")
async def get_patch_detail(plan_id: str):
    """Get detailed patch information"""
    patch = next((p for p in live_generator.patches if p['id'] == plan_id), None)
    if not patch:
        return {"error": "Not found"}

    created_at = patch.get("created_at")
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()

    affected_hosts = patch.get('affected_hosts')
    if not affected_hosts:
        affected_hosts = [f"host-{i}" for i in range(1, min(6, patch['systems']))]

    health_checks = patch.get('health_checks')
    if not health_checks:
        health_checks = ["CPU < 80%", "Memory < 70%", "Service response < 200ms"]

    return {
        "id": patch['id'],
        "name": patch['name'],
        "systems": patch.get('systems'),
        "status": patch.get('status'),
        "progress": patch.get('progress'),
        "risk_score": patch.get('risk_score'),
        "created_at": created_at,
        "incident_id": patch.get('incident_id'),
        "canary_phases": patch.get('phases', []),
        "affected_hosts": affected_hosts,
        "rollback_plan": "Automated rollback within 10 minutes if health checks fail",
        "health_checks": health_checks
    }

@app.get("/api/forecasts")
async def get_forecasts():
    """Return real-time forecast data from PredictiveOps analysis"""
    return live_generator.forecast_cache

def extract_action_target(action: dict) -> str:
    """
    Extract meaningful target information from action data.
    Checks params, description, and fallback fields to provide useful target context.
    """
    # Check if params exist and extract specific target information
    params = action.get('params', {})

    # Try to get host first (most common target)
    if params.get('host'):
        host = params['host']
        # If service is specified, include it
        if params.get('service'):
            return f"{host}/{params['service']}"
        return host

    # Check for service name (restart_service actions)
    if params.get('service'):
        return params['service']

    # Check for patch ID or patch name
    if params.get('patch_id'):
        return f"Patch: {params['patch_id']}"
    if params.get('patch'):
        return f"Patch: {params['patch']}"

    # Check for target in action itself
    if action.get('target'):
        return action['target']

    # Extract from description if possible
    description = action.get('description', '')
    if 'on' in description:
        # Try to extract target from "Executed X on Y" pattern
        parts = description.split(' on ')
        if len(parts) > 1:
            return parts[1].strip()

    # Fallback to incident context
    incident_id = action.get('incident_id')
    if incident_id:
        return f"Incident: {incident_id}"

    # Last resort
    return "System"


@app.get("/api/audit-logs")
async def get_audit_logs(incident_id: str = None):
    """
    Return audit logs, optionally filtered by incident
    If incident_id provided: return incident-specific actions
    Otherwise: return global executor logs
    """
    logs = []

    if incident_id:
        # Return incident-specific audit logs
        incident = kb.get_incident(incident_id)
        if not incident:
            return []

        # Get incident-specific actions
        incident_actions = incident.get('incident_actions', [])

        for i, action in enumerate(incident_actions):
            # Format action type and status
            action_type = action.get('action_type', action.get('type', 'Unknown'))
            formatted_action = humanize_action_type(action_type)

            status = action.get('status', 'unknown')
            formatted_status = humanize_status(status)

            # Format timestamp
            action_timestamp = action.get('timestamp')
            formatted_time = "N/A"
            if action_timestamp:
                try:
                    if isinstance(action_timestamp, int):
                        from datetime import datetime as dt
                        dt_obj = dt.fromtimestamp(action_timestamp)
                        formatted_time = format_datetime(dt_obj, 'full')
                    else:
                        formatted_time = format_datetime(action_timestamp, 'full')
                except:
                    formatted_time = str(action_timestamp)

            # FIX: Extract meaningful target instead of hardcoded "N/A"
            target = extract_action_target(action)

            logs.append({
                "id": action.get('action_id', f"ACT-{i:03d}"),
                "agent": action.get('agent', 'Unknown'),
                "action": formatted_action,
                "target": target,
                "status": formatted_status.lower(),
                "time": formatted_time,
                "incident_id": incident_id
            })

    else:
        # Return ALL incident actions from all incidents (most recent 50)
        all_incidents = list(kb.incident_memory.values())
        all_incidents.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        action_count = 0
        for incident in all_incidents:
            if action_count >= 50:
                break

            incident_id = incident.get('incident_id')
            incident_actions = incident.get('incident_actions', [])
            for action in incident_actions:
                if action_count >= 50:
                    break

                # Format action type and status
                action_type = action.get('action_type', action.get('type', 'Unknown'))
                formatted_action = humanize_action_type(action_type)

                status = action.get('status', 'unknown')
                formatted_status = humanize_status(status)

                # Format timestamp
                action_timestamp = action.get('timestamp')
                formatted_time = "N/A"
                if action_timestamp:
                    try:
                        if isinstance(action_timestamp, int):
                            from datetime import datetime as dt
                            dt_obj = dt.fromtimestamp(action_timestamp)
                            formatted_time = format_datetime(dt_obj, 'full')
                        else:
                            formatted_time = format_datetime(action_timestamp, 'full')
                    except:
                        formatted_time = str(action_timestamp)

                # FIX: Extract meaningful target for global view too
                target = extract_action_target(action)

                logs.append({
                    "id": action.get('action_id', f"ACT-{action_count:03d}"),
                    "agent": action.get('agent', 'Unknown'),
                    "action": formatted_action,
                    "target": target,
                    "status": formatted_status.lower(),
                    "time": formatted_time,
                    "incident_id": incident_id
                })
                action_count += 1

    return logs[::-1]

@app.post("/api/kill-switch/toggle")
async def toggle_kill_switch():
    """Toggle the kill switch for autonomous actions"""
    state = live_generator.toggle_kill_switch()
    return {
        "active": state,
        "message": "Kill switch activated - all autonomous actions paused" if state else "Kill switch deactivated - autonomous actions resumed"
    }

@app.get("/api/kill-switch/status")
async def get_kill_switch_status():
    """Get current kill switch status"""
    return {"active": live_generator.get_kill_switch_state()}

@app.post("/api/simulation/start")
async def start_simulation():
    """Start incident generation simulation"""
    success = live_generator.start_simulation()
    if success:
        return {
            "status": "started",
            "running": True,
            "message": "Incident simulation started - generating incidents every 30-60 seconds"
        }
    return {
        "status": "already_running",
        "running": True,
        "message": "Simulation is already active"
    }

@app.post("/api/simulation/stop")
async def stop_simulation():
    """Stop incident generation simulation"""
    success = live_generator.stop_simulation()
    if success:
        return {
            "status": "stopped",
            "running": False,
            "message": "Incident simulation stopped - no new incidents will be generated"
        }
    return {
        "status": "already_stopped",
        "running": False,
        "message": "Simulation is already inactive"
    }

@app.get("/api/simulation/status")
async def get_simulation_status():
    """Get current simulation running state"""
    return {
        "running": live_generator.get_simulation_state()
    }

@app.post("/api/terminal-output-mode")
async def set_terminal_output_mode(data: dict):
    """Change terminal output mode: full, selective, or none"""
    from config.terminal_logger import terminal_logger
    mode = data.get("mode", "")
    if mode not in ["full", "selective", "none"]:
        return {"error": "Invalid mode. Must be 'full', 'selective', or 'none'"}

    terminal_logger.set_output_mode(mode)
    return {
        "mode": mode,
        "message": f"Terminal output mode set to '{mode}'"
    }

@app.get("/api/terminal-output-mode")
async def get_terminal_output_mode():
    """Get current terminal output mode"""
    from config.terminal_logger import terminal_logger
    return {
        "mode": terminal_logger.get_output_mode()
    }

@app.get("/api/logs")
async def get_logs(limit: int = 1000, log_type: str = None):
    """Get recent system logs for terminal viewer, optionally filtered by type"""
    from config.terminal_logger import terminal_logger
    logs = terminal_logger.get_logs(limit=limit, log_type=log_type)
    return {
        "logs": logs,
        "count": len(logs),
        "filter": log_type or "ALL"
    }

@app.post("/api/logs/clear")
async def clear_logs():
    """Clear all logs from the terminal logger buffer"""
    from config.terminal_logger import terminal_logger
    terminal_logger.clear_logs()
    return {"status": "cleared"}

if __name__ == "__main__":
    import uvicorn
    # FIX: Explicitly disable reload to prevent state reset
    # Auto-reload causes module reimport which resets live_generator instance
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
