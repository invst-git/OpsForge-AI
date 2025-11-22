import React, { useState, useEffect } from 'react';
import { Download, X, ChevronUp, ChevronDown } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

export default function Incidents() {
  const [incidents, setIncidents] = useState([]);
  const [filter, setFilter] = useState('all');
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [whyTraceExpanded, setWhyTraceExpanded] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      const fetchId = Date.now();
      console.log(`[Incidents ${fetchId}] 🔄 Fetching...`);

      try {
        const res = await fetch(`${API_BASE}/incidents`);
        const data = await res.json();

        console.log(`[Incidents ${fetchId}] 📊 Received ${data.length} incidents`);
        setIncidents(prev => (Array.isArray(data) && (data.length > 0 || prev.length === 0)) ? data : prev);
        console.log(`[Incidents ${fetchId}] ✅ State updated`);
      } catch (error) {
        console.error(`[Incidents ${fetchId}] ❌ Error:`, error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 3000);

    return () => clearInterval(interval);
  }, []);

  const exportCSV = async () => {
    // Fetch full details for all incidents to include comprehensive data
    const detailedIncidents = await Promise.all(
      incidents.map(async (inc) => {
        try {
          const res = await fetch(`${API_BASE}/incidents/${inc.id}`);
          return await res.json();
        } catch (error) {
          console.error(`Failed to fetch details for ${inc.id}:`, error);
          return null;
        }
      })
    );

    // Helper to escape CSV fields containing commas or quotes
    const escapeCSV = (field) => {
      if (field === null || field === undefined) return '';
      const str = String(field);
      if (str.includes(',') || str.includes('"') || str.includes('\n')) {
        return `"${str.replace(/"/g, '""')}"`;
      }
      return str;
    };

    // Helper to format timestamp
    const formatTimestamp = (timestamp) => {
      if (!timestamp) return 'N/A';
      if (typeof timestamp === 'string') {
        // Backend already returns ISO-like strings; preserve as-is to avoid timezone shifts
        return timestamp;
      }
      try {
        const date = new Date(timestamp);
        return Number.isNaN(date.getTime()) ? String(timestamp) : date.toISOString();
      } catch (e) {
        return String(timestamp);
      }
    };

    // Helper to calculate duration
    const calculateDuration = (created, resolved) => {
      if (!created || !resolved) return 'N/A';
      try {
        const start = new Date(created);
        const end = new Date(resolved);
        const diffMs = end - start;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const remainingMins = diffMins % 60;
        if (diffHours > 0) {
          return `${diffHours}h ${remainingMins}m`;
        }
        return `${diffMins}m`;
      } catch (e) {
        return 'N/A';
      }
    };

    // Build comprehensive CSV with headers
    const headers = [
      'Incident ID',
      'Title',
      'Severity',
      'Status',
      'Created Timestamp',
      'Resolved Timestamp',
      'Duration',
      'Alert Count',
      'Agents Involved',
      'Actions Taken',
      'Processing State',
      'Root Cause Summary',
      'Affected Components',
      'Correlation Score',
      'Confidence Level'
    ];

    const rows = detailedIncidents
      .filter(detail => detail !== null)
      .map(detail => {
        const createdTime = detail.createdAt || detail.created_at || 'N/A';

        // Prefer resolvedAt / resolved_at when present, regardless of status casing
        const resolvedTimeRaw = detail.resolvedAt || detail.resolved_at || null;

        const duration =
          resolvedTimeRaw
            ? calculateDuration(createdTime, resolvedTimeRaw)
            : (detail.status && detail.status.toLowerCase() === 'resolved' ? 'N/A' : 'In Progress');

        const rootCauseSummarySource =
          detail.root_cause_summary ||
          detail.rootCauseSummary ||
          detail.why_trace?.analysis ||
          detail.rootCause ||
          'N/A';

        const rootCauseSummary = rootCauseSummarySource
          .split('\n')[0] // First line only for summary
          .substring(0, 200); // Limit to 200 chars

        const affectedComponents = (detail.why_trace?.affected_components || []).join('; ');

        const correlationScore = detail.why_trace && detail.why_trace.correlation_score !== undefined && detail.why_trace.correlation_score !== null
          ? detail.why_trace.correlation_score
          : '';

        const confidenceLevel = detail.why_trace && detail.why_trace.confidence !== undefined && detail.why_trace.confidence !== null
          ? detail.why_trace.confidence
          : '';

        return [
          detail.id,
          detail.title || 'N/A',
          detail.severity || 'medium',
          detail.status || 'investigating',
          formatTimestamp(createdTime),
          formatTimestamp(resolvedTimeRaw),
          duration,
          detail.alerts?.length || 0,
          (detail.agents_involved || []).join('; ') || 'N/A',
          detail.audit_logs?.length || 0,
          detail.processingState || detail.processing_state || 'N/A',
          rootCauseSummary,
          affectedComponents || '',
          correlationScore,
          confidenceLevel
        ].map(escapeCSV);
      });

    const csv = [headers, ...rows]
      .map(row => row.join(','))
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `incidents_detailed_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const viewDetail = async (incidentId) => {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}`);
    setSelectedIncident(await res.json());
  };

  // PHASE 4 TASK 4.3: Filter incidents by status
  // Status values match directly: 'investigating', 'in_progress', 'resolved'
  // With real processing states (Phase 1), status transitions now work properly
  const filtered = filter === 'all' ? incidents : incidents.filter(i => i.status === filter);

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Incidents</h1>
        <button className="btn btn-primary" onClick={exportCSV}>
          <Download size={16} /> Export CSV
        </button>
      </div>

      <div className="card">
        <div className="filters">
          <button className={filter === 'all' ? 'filter-btn active' : 'filter-btn'} onClick={() => setFilter('all')}>All</button>
          <button className={filter === 'resolved' ? 'filter-btn active' : 'filter-btn'} onClick={() => setFilter('resolved')}>Resolved</button>
          <button className={filter === 'in_progress' ? 'filter-btn active' : 'filter-btn'} onClick={() => setFilter('in_progress')}>In Progress</button>
          <button className={filter === 'investigating' ? 'filter-btn active' : 'filter-btn'} onClick={() => setFilter('investigating')}>Investigating</button>
        </div>

        <div className="incident-table">
          {filtered.map(incident => (
            <div key={incident.id} className="incident-row-full" onClick={() => viewDetail(incident.id)}>
              <div className="incident-id-col">{incident.id}</div>
              <div className="incident-details-col">
                <div className="incident-title-text">{incident.title}</div>
                <div className="incident-meta">
                  <span className={`severity-badge ${incident.severity}`}>{incident.severity}</span>
                  <span className={`status-badge ${incident.status}`}>{incident.status}</span>
                </div>
              </div>
              <div className="incident-time-col">{incident.time}</div>
            </div>
          ))}
        </div>
      </div>

      {selectedIncident && (
        <div className="modal-overlay" onClick={() => setSelectedIncident(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{selectedIncident.id}</h2>
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
                {selectedIncident.timeline?.map((e, i) => (
                  <div key={i} className="timeline-event">
                    <span className="event-time">{e.time}</span>
                    <span>{e.event}</span>
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
    </div>
  );
}
