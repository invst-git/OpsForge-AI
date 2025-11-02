import React, { useState, useEffect } from 'react';
import { Download } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      const res = await fetch(`${API_BASE}/audit-logs`);
      setLogs(await res.json());
    };
    fetchData();
    const interval = setInterval(fetchData, 3000); // Standardized to 3000ms
    return () => clearInterval(interval);
  }, []);

  const exportCSV = () => {
    // Helper to escape CSV fields containing commas or quotes
    const escapeCSV = (field) => {
      if (field === null || field === undefined) return '';
      const str = String(field);
      if (str.includes(',') || str.includes('"') || str.includes('\n')) {
        return `"${str.replace(/"/g, '""')}"`;
      }
      return str;
    };

    // Build comprehensive CSV with headers including incident context
    const headers = [
      'Action ID',
      'Timestamp',
      'Agent',
      'Action Type',
      'Target',
      'Status',
      'Incident ID'
    ];

    const rows = logs.map(log => [
      log.id,
      log.time, // Already formatted timestamp
      log.agent,
      log.action,
      log.target,
      log.status,
      log.incident_id || 'N/A'
    ].map(escapeCSV));

    const csv = [headers, ...rows]
      .map(row => row.join(','))
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_logs_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Audit Logs</h1>
        <button className="btn btn-primary" onClick={exportCSV}>
          <Download size={16} /> Export CSV
        </button>
      </div>

      <div className="card">
        <div className="audit-table">
          <div className="audit-header">
            <div>ID</div>
            <div>Agent</div>
            <div>Action</div>
            <div>Target</div>
            <div>Status</div>
            <div>Time</div>
            <div>Incident</div>
          </div>
          {logs.map(log => (
            <div key={log.id} className="audit-row">
              <div>{log.id}</div>
              <div>{log.agent}</div>
              <div>{log.action}</div>
              <div>{log.target}</div>
              <div><span className={`status-badge ${log.status}`}>{log.status}</span></div>
              <div>{log.time}</div>
              <div style={{ fontSize: '12px', color: '#888' }}>{log.incident_id || '-'}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
