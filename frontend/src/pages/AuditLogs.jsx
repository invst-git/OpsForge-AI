import React, { useState, useEffect } from 'react';
import { Download } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      const res = await fetch(`${API_BASE}/audit-logs`);
      setLogs(await res.json());
    };
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const exportCSV = () => {
    const csv = [
      ['ID', 'Agent', 'Action', 'Target', 'Status', 'Time'],
      ...logs.map(l => [l.id, l.agent, l.action, l.target, l.status, l.time])
    ].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_logs_${Date.now()}.csv`;
    a.click();
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
          </div>
          {logs.map(log => (
            <div key={log.id} className="audit-row">
              <div>{log.id}</div>
              <div>{log.agent}</div>
              <div>{log.action}</div>
              <div>{log.target}</div>
              <div><span className={`status-badge ${log.status}`}>{log.status}</span></div>
              <div>{log.time}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}