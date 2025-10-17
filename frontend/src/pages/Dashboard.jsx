import React, { useState, useEffect } from 'react';
import { ArrowRight, TrendingDown, Clock, CheckCircle, X } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

export default function Dashboard() {
  const [metrics, setMetrics] = useState({});
  const [agents, setAgents] = useState([]);
  const [recentIncidents, setRecentIncidents] = useState([]);
  const [recentActions, setRecentActions] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);

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

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setAgents(prev => updateRelativeTimes(prev));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

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
          <div className="metric-change positive">↓ 50-70% target</div>
        </div>
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">MTTR Reduction</span>
            <Clock size={20} className="metric-icon success" />
          </div>
          <div className="metric-value">{metrics.mttrReduction?.toFixed(1) || 0}%</div>
          <div className="metric-change positive">↓ 30-45% target</div>
        </div>
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Tasks Automated</span>
            <CheckCircle size={20} className="metric-icon success" />
          </div>
          <div className="metric-value">{metrics.tasksAutomated || 0}%</div>
          <div className="metric-change positive">↑ ~8hrs saved/week</div>
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
            <button className="btn-link">
              View All <ArrowRight size={16} />
            </button>
          </div>
          <div className="incident-list">
            {recentIncidents.map(incident => (
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
                    <span>{incident.relative_time}</span>
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
        </div>
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
                <h3>Why-Trace Analysis</h3>
                <p>{selectedIncident.why_trace}</p>
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
            </div>
          </div>
        </div>
      )}
    </div>
  );
}