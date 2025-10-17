import React, { useState, useEffect } from 'react';
import { Download, X } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

export default function Incidents() {
  const [incidents, setIncidents] = useState([]);
  const [filter, setFilter] = useState('all');
  const [selectedIncident, setSelectedIncident] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      const fetchId = Date.now();
      console.log(`[Incidents ${fetchId}] 🔄 Fetching...`);

      try {
        const res = await fetch(`${API_BASE}/incidents`);
        const data = await res.json();

        console.log(`[Incidents ${fetchId}] 📊 Received ${data.length} incidents`);
        setIncidents(data);
        console.log(`[Incidents ${fetchId}] ✅ State updated`);
      } catch (error) {
        console.error(`[Incidents ${fetchId}] ❌ Error:`, error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 3000);

    return () => clearInterval(interval);
  }, []);

  const exportCSV = () => {
    const csv = [
      ['ID', 'Title', 'Severity', 'Status', 'Time'],
      ...incidents.map(i => [i.id, i.title, i.severity, i.status, i.time])
    ].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `incidents_${Date.now()}.csv`;
    a.click();
  };

  const viewDetail = async (incidentId) => {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}`);
    setSelectedIncident(await res.json());
  };

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
                <h3>Why-Trace</h3>
                <p>{selectedIncident.why_trace}</p>
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
            </div>
          </div>
        </div>
      )}
    </div>
  );
}