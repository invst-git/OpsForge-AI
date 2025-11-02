import React, { useState, useEffect } from 'react';
import { ArrowRight, TrendingDown, Clock, CheckCircle, X, ChevronUp, ChevronDown } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

export default function Dashboard() {
  const [metrics, setMetrics] = useState({});
  const [agents, setAgents] = useState([]);
  const [recentIncidents, setRecentIncidents] = useState([]);
  const [recentActions, setRecentActions] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);

  // PHASE 5 FIX: State for viewing all items in modals
  const [showAllIncidents, setShowAllIncidents] = useState(false);
  const [showAllActions, setShowAllActions] = useState(false);
  const [whyTraceExpanded, setWhyTraceExpanded] = useState(false);

  // Debug: Log current state whenever it changes
  useEffect(() => {
    console.log('🎨 Dashboard State:', {
      metricsKeys: Object.keys(metrics),
      agentsCount: agents.length,
      incidentsCount: recentIncidents.length,
      actionsCount: recentActions.length
    });
  }, [metrics, agents, recentIncidents, recentActions]);

  const getRelativeTime = (isoTime) => {
    if (!isoTime || isoTime === 'N/A') return 'N/A';
    try {
      const delta = Date.now() - new Date(isoTime).getTime();
      const seconds = Math.floor(delta / 1000);
      if (seconds < 60) return 'Just now';
      const minutes = Math.floor(seconds / 60);
      if (minutes < 60) return `${minutes} min ago`;
      const hours = Math.floor(minutes / 60);
      if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
      const days = Math.floor(hours / 24);
      return `${days} day${days > 1 ? 's' : ''} ago`;
    } catch {
      return isoTime;
    }
  };

  const updateRelativeTimes = (agentsList) => {
    return agentsList.map(agent => ({
      ...agent,
      lastAction: agent.lastActionTime ? getRelativeTime(agent.lastActionTime) : agent.lastAction
    }));
  };

  const fetchData = async () => {
    const fetchId = Date.now();
    console.log(`[${fetchId}] 🔄 Starting fetch...`);

    try {
      const [metricsRes, agentsRes, incidentsRes, actionsRes] = await Promise.all([
        fetch(`${API_BASE}/metrics`),
        fetch(`${API_BASE}/agents`),
        fetch(`${API_BASE}/incidents`),
        fetch(`${API_BASE}/actions/recent`)
      ]);

      console.log(`[${fetchId}] ✅ Responses received`);

      const [metricsData, agentsData, incidentsData, actionsData] = await Promise.all([
        metricsRes.json(),
        agentsRes.json(),
        incidentsRes.json(),
        actionsRes.json()
      ]);

      console.log(`[${fetchId}] 📊 Data parsed:`, {
        metrics: Object.keys(metricsData).length,
        agents: agentsData.length,
        incidents: incidentsData.length,
        actions: actionsData.length
      });

      setMetrics(metricsData);
      setAgents(agentsData);
      setRecentIncidents(incidentsData);
      setRecentActions(actionsData);

      console.log(`[${fetchId}] ✅ State updated successfully`);

    } catch (error) {
      console.error(`[${fetchId}] ❌ Fetch error:`, error);
    }
  };

  // Safer fetch that keeps last-good state if partial updates fail
  const fetchDataSafe = async () => {
    const fetchId = Date.now();
    console.log(`[${fetchId}] dY", Starting fetch (safe)...`);
    const requests = [
      fetch(`${API_BASE}/metrics`).then(r => r.json()),
      fetch(`${API_BASE}/agents`).then(r => r.json()),
      fetch(`${API_BASE}/incidents`).then(r => r.json()),
      fetch(`${API_BASE}/actions/recent`).then(r => r.json())
    ];
    const [m, a, i, act] = await Promise.allSettled(requests);
    if (m.status === 'fulfilled') {
      setMetrics(prev => (m.value && Object.keys(m.value).length > 0 ? m.value : prev));
    }
    if (a.status === 'fulfilled') {
      setAgents(prev => (Array.isArray(a.value) && (a.value.length > 0 || prev.length === 0)) ? a.value : prev);
    }
    if (i.status === 'fulfilled') {
      setRecentIncidents(prev => (Array.isArray(i.value) && (i.value.length > 0 || prev.length === 0)) ? i.value : prev);
    }
    if (act.status === 'fulfilled') {
      setRecentActions(prev => (Array.isArray(act.value) && (act.value.length > 0 || prev.length === 0)) ? act.value : prev);
    }
  };

  useEffect(() => {
    fetchDataSafe();
    const interval = setInterval(fetchDataSafe, 3000);
    return () => clearInterval(interval);
  }, []);

  // PHASE 4 TASK 4.1: Remove unnecessary 1-second recalculation
  // Relative times are already provided by backend and refreshed every 3 seconds with fetchData
  // No need to recalculate every second, which causes flickering and instability
  // useEffect(() => {
  //   const interval = setInterval(() => {
  //     setAgents(prev => updateRelativeTimes(prev));
  //   }, 1000);
  //   return () => clearInterval(interval);
  // }, []);

  const viewIncidentDetail = async (incidentId) => {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}`);
    const data = await res.json();
    setSelectedIncident(data);
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
      </div>

      <div className="metrics-grid-3">
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Alerts Reduced</span>
            <TrendingDown size={20} className="metric-icon success" />
          </div>
          <div className="metric-value">{metrics.alertsReduced?.toFixed(1) || 0}%</div>
          <div className="metric-change positive">Reducing alert noise</div>
        </div>
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">MTTR Reduction</span>
            <Clock size={20} className="metric-icon success" />
          </div>
          <div className="metric-value">{metrics.mttrReduction?.toFixed(1) || 0}%</div>
          <div className="metric-change positive">Faster incident resolution</div>
        </div>
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Tasks Automated</span>
            <CheckCircle size={20} className="metric-icon success" />
          </div>
          <div className="metric-value">{metrics.tasksAutomated || 0}</div>
          <div className="metric-change positive">Automating operations</div>
        </div>
      </div>

      <div className="quick-stats">
        <div className="stat-item">
          <span className="stat-value">{metrics.activeIncidents || 0}</span>
          <span className="stat-label">Active Incidents</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{metrics.patchesPending || 0}</span>
          <span className="stat-label">Patches Pending</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{metrics.upcomingRisks || 0}</span>
          <span className="stat-label">Predicted Risks</span>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="card">
          <div className="card-header">
            <div className="card-title">Agent Status</div>
          </div>
          <div className="agent-list">
            {agents.map(agent => (
              <div key={agent.name} className="agent-item">
                <div className="agent-info">
                  <div className="agent-name-status">
                    <span className="agent-name-text">{agent.name}</span>
                    <span className={`status-badge ${agent.status}`}>{agent.status}</span>
                  </div>
                  <div className="agent-meta">
                    <span>{agent.actions} actions</span>
                    <span>•</span>
                    <span>Last: {agent.lastAction}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">Recent Incidents</div>
            {/* PHASE 5 FIX: Show View All button if more than 5 incidents */}
            {recentIncidents.length > 5 && (
              <button className="btn-link" onClick={() => setShowAllIncidents(true)}>
                View All <ArrowRight size={16} />
              </button>
            )}
          </div>
          <div className="incident-list">
            {/* PHASE 5 FIX: Truncate to 5 items in dashboard view */}
            {recentIncidents.slice(0, 5).map(incident => (
              <div key={incident.id} className="incident-row" onClick={() => viewIncidentDetail(incident.id)}>
                <div className="incident-content">
                  <div className="incident-id-title">
                    <span className="incident-id-text">{incident.id}</span>
                    <span className={`severity-badge ${incident.severity}`}>{incident.severity}</span>
                  </div>
                  <div className="incident-title-text">{incident.title}</div>
                  <div className="incident-meta">
                    <span className={`status-text ${incident.status}`}>{incident.status}</span>
                    <span>•</span>
                    <span>{incident.time}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title">Recent Actions</div>
          {/* PHASE 5 FIX: Show View More button if more than 5 actions */}
          {recentActions.length > 5 && (
            <button className="btn-link" onClick={() => setShowAllActions(true)}>
              View More <ArrowRight size={16} />
            </button>
          )}
        </div>
        <div className="action-timeline">
          {/* PHASE 5 FIX: Truncate to 5 items in dashboard view */}
          {recentActions.slice(0, 5).map((action, idx) => (
            <div key={idx} className="timeline-item">
              <div className="timeline-marker"></div>
              <div className="timeline-content">
                <div className="timeline-agent">{action.agent}</div>
                <div className="timeline-action">{action.action}</div>
                <div className="timeline-time">{action.time}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {selectedIncident && (
        <div className="modal-overlay" onClick={() => setSelectedIncident(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Incident Details: {selectedIncident.id}</h2>
              <button className="icon-btn" onClick={() => setSelectedIncident(null)}>
                <X size={20} />
              </button>
            </div>
            <div className="modal-body">
              <div className="detail-section">
                <div
                  onClick={() => setWhyTraceExpanded(!whyTraceExpanded)}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '12px',
                    cursor: 'pointer',
                    padding: '8px',
                    borderRadius: '4px',
                    backgroundColor: '#f0f0f0',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#e0e0e0'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#f0f0f0'}
                >
                  <h3 style={{ margin: 0 }}>Why-Trace Analysis</h3>
                  {whyTraceExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                </div>
                <div style={{
                  maxHeight: whyTraceExpanded ? 'none' : '200px',
                  overflowY: whyTraceExpanded ? 'visible' : 'auto',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  padding: '12px',
                  backgroundColor: '#fafafa'
                }}>
                  {(() => {
                    const rawAnalysis = selectedIncident.why_trace?.analysis || selectedIncident.why_trace || 'N/A';
                    const sections = [];
                    let currentSection = null;

                    // Parse the analysis into structured sections
                    rawAnalysis.split('\n').forEach(line => {
                      const trimmed = line.trim();

                      // Detect section headers (all caps)
                      if (/^[A-Z\s]+$/.test(trimmed) && trimmed.length > 0 && !/^\d/.test(trimmed)) {
                        if (currentSection) sections.push(currentSection);
                        currentSection = { header: trimmed, lines: [] };
                      } else if (currentSection && trimmed) {
                        currentSection.lines.push(trimmed);
                      }
                    });
                    if (currentSection) sections.push(currentSection);

                    return sections.map((section, idx) => (
                      <div key={idx} style={{
                        marginBottom: '16px',
                        paddingBottom: '12px',
                        borderBottom: idx < sections.length - 1 ? '1px solid #e0e0e0' : 'none'
                      }}>
                        <div style={{
                          fontWeight: 'bold',
                          fontSize: '14px',
                          marginBottom: '8px',
                          color: '#1a1a1a'
                        }}>
                          {section.header}
                        </div>
                        <div style={{ lineHeight: '1.7', fontSize: '13px', color: '#444' }}>
                          {section.lines.map((line, lineIdx) => (
                            <div key={lineIdx} style={{
                              marginTop: lineIdx > 0 ? '4px' : '0'
                            }}>
                              {line}
                            </div>
                          ))}
                        </div>
                      </div>
                    ));
                  })()}
                </div>
              </div>
              <div className="detail-section">
                <h3>Timeline</h3>
                {selectedIncident.timeline?.map((event, idx) => (
                  <div key={idx} className="timeline-event">
                    <span className="event-time">{event.time}</span>
                    <span className="event-text">{event.event}</span>
                  </div>
                ))}
              </div>

              {/* PHASE 4 TASK 4.4: Display incident-specific audit logs */}
              {selectedIncident.audit_logs && selectedIncident.audit_logs.length > 0 && (
                <div className="detail-section">
                  <h3>Audit Logs</h3>
                  <div style={{
                    maxHeight: '300px',
                    overflowY: 'auto',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    padding: '8px'
                  }}>
                    {selectedIncident.audit_logs.map((log, idx) => (
                      <div key={idx} style={{
                        padding: '12px 0',
                        borderBottom: idx < selectedIncident.audit_logs.length - 1 ? '1px solid #eee' : 'none',
                        fontSize: '14px',
                        lineHeight: '1.5'
                      }}>
                        <div style={{ fontWeight: 'bold', color: '#333', marginBottom: '4px' }}>
                          {log.agent}: {log.action}
                        </div>
                        <div style={{ color: '#666', fontSize: '12px', marginBottom: '6px' }}>
                          {log.description}
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#999', fontSize: '12px' }}>
                          <span>
                            Status: <span style={{
                              backgroundColor: log.status === 'completed' ? '#d4edda' : '#fff3cd',
                              padding: '2px 6px',
                              borderRadius: '3px',
                              color: log.status === 'completed' ? '#155724' : '#856404',
                              fontWeight: '500'
                            }}>
                              {log.status}
                            </span>
                          </span>
                          <span style={{ textAlign: 'right' }}>{log.time}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* PHASE 5 FIX: Modal to show all incidents */}
      {showAllIncidents && (
        <div className="modal-overlay" onClick={() => setShowAllIncidents(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '600px', maxHeight: '80vh', overflowY: 'auto' }}>
            <div className="modal-header">
              <h2>All Incidents ({recentIncidents.length})</h2>
              <button className="icon-btn" onClick={() => setShowAllIncidents(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="modal-body">
              <div className="incident-list">
                {recentIncidents.map(incident => (
                  <div
                    key={incident.id}
                    className="incident-row"
                    onClick={() => {
                      viewIncidentDetail(incident.id);
                      setShowAllIncidents(false);
                    }}
                  >
                    <div className="incident-content">
                      <div className="incident-id-title">
                        <span className="incident-id-text">{incident.id}</span>
                        <span className={`severity-badge ${incident.severity}`}>{incident.severity}</span>
                      </div>
                      <div className="incident-title-text">{incident.title}</div>
                      <div className="incident-meta">
                        <span className={`status-text ${incident.status}`}>{incident.status}</span>
                        <span>•</span>
                        <span>{incident.time}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* PHASE 5 FIX: Modal to show all actions */}
      {showAllActions && (
        <div className="modal-overlay" onClick={() => setShowAllActions(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '600px', maxHeight: '80vh', overflowY: 'auto' }}>
            <div className="modal-header">
              <h2>All Actions ({recentActions.length})</h2>
              <button className="icon-btn" onClick={() => setShowAllActions(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="modal-body">
              <div className="action-timeline">
                {recentActions.map((action, idx) => (
                  <div key={idx} className="timeline-item">
                    <div className="timeline-marker"></div>
                    <div className="timeline-content">
                      <div className="timeline-agent">{action.agent}</div>
                      <div className="timeline-action">{action.action}</div>
                      <div className="timeline-time">{action.time}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
