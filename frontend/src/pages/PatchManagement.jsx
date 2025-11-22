import React, { useState, useEffect } from 'react';
import { CheckCircle, Clock, XCircle, AlertCircle } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

export default function PatchManagement() {
  const [patches, setPatches] = useState([]);
  const [selectedPatch, setSelectedPatch] = useState(null);

  const getRelativeTime = (isoTime) => {
    if (!isoTime) return null;
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
      return null;
    }
  };

  const formatDateTime = (isoTime) => {
    if (!isoTime) return 'N/A';
    try {
      return new Date(isoTime).toLocaleString();
    } catch {
      return isoTime;
    }
  };

  const getRiskLabel = (score) => {
    if (typeof score !== 'number') return 'N/A';
    if (score < 0.2) return 'Low';
    if (score < 0.35) return 'Medium';
    return 'High';
  };

  useEffect(() => {
    const fetchData = async () => {
      const res = await fetch(`${API_BASE}/patches`);
      setPatches(await res.json());
    };
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  const viewPatchDetail = async (patchId) => {
    const res = await fetch(`${API_BASE}/patches/${patchId}`);
    setSelectedPatch(await res.json());
  };

  const totalSystems = patches.reduce((sum, p) => sum + p.systems, 0);
  const patchedCount = patches
    .filter((p) => p.status === 'completed')
    .reduce((sum, p) => sum + p.systems, 0);
  const pendingCount = patches.filter((p) =>
    ['pending', 'in_progress', 'paused'].includes(p.status)
  ).length;
  const failedCount = patches.filter((p) => p.status === 'failed').length;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Patch Management</h1>
      </div>

      <div className="metrics-grid-4">
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Total Systems</span>
            <AlertCircle
              size={20}
              className="metric-icon"
              style={{ color: '#6c757d' }}
            />
          </div>
          <div className="metric-value">{totalSystems}</div>
        </div>
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Patched</span>
            <CheckCircle size={20} className="metric-icon success" />
          </div>
          <div className="metric-value success">{patchedCount}</div>
        </div>
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Pending</span>
            <Clock size={20} className="metric-icon warning" />
          </div>
          <div className="metric-value warning">{pendingCount}</div>
        </div>
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Failed</span>
            <XCircle size={20} className="metric-icon danger" />
          </div>
          <div className="metric-value danger">{failedCount}</div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title">Patch Plans</div>
        </div>
        <div className="patch-list">
          {patches.map((patch) => (
            <div
              key={patch.id}
              className="patch-item"
              onClick={() => viewPatchDetail(patch.id)}
            >
              <div className="patch-info">
                <div className="patch-id-name">
                  <span className="patch-id">{patch.id}</span>
                  <span className="patch-name">{patch.name}</span>
                </div>
                <div className="patch-meta">
                  <span>{patch.systems} systems</span>
                  <span>·</span>
                  <span className={`status-badge ${patch.status}`}>
                    {patch.status.replace('_', ' ')}
                  </span>
                  {typeof patch.risk_score === 'number' && (
                    <>
                      <span>·</span>
                      <span>Risk: {getRiskLabel(patch.risk_score)}</span>
                    </>
                  )}
                  {patch.created_at && getRelativeTime(patch.created_at) && (
                    <>
                      <span>·</span>
                      <span>{getRelativeTime(patch.created_at)}</span>
                    </>
                  )}
                </div>
              </div>
              <div className="patch-progress">
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${patch.progress}%` }}
                  ></div>
                </div>
                <span className="progress-text">{patch.progress}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {selectedPatch && (
        <div
          className="modal-overlay"
          onClick={() => setSelectedPatch(null)}
        >
          <div
            className="modal"
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: '600px' }}
          >
            <div className="modal-header">
              <h2>{selectedPatch.name}</h2>
              <button
                className="icon-btn"
                onClick={() => setSelectedPatch(null)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="detail-section">
                <h3>Summary</h3>
                <p>
                  <strong>Plan ID:</strong> {selectedPatch.id}
                </p>
                {selectedPatch.status && (
                  <p>
                    <strong>Status:</strong>{' '}
                    {selectedPatch.status.replace('_', ' ')}
                  </p>
                )}
                {typeof selectedPatch.risk_score === 'number' && (
                  <p>
                    <strong>Risk:</strong>{' '}
                    {getRiskLabel(selectedPatch.risk_score)}
                  </p>
                )}
                {typeof selectedPatch.systems === 'number' && (
                  <p>
                    <strong>Target Systems:</strong> {selectedPatch.systems}
                  </p>
                )}
                {selectedPatch.created_at && (
                  <p>
                    <strong>Created:</strong>{' '}
                    {formatDateTime(selectedPatch.created_at)}
                  </p>
                )}
                {selectedPatch.incident_id && (
                  <p>
                    <strong>Source Incident:</strong>{' '}
                    {selectedPatch.incident_id}
                  </p>
                )}
              </div>

              <div className="detail-section">
                <h3>Canary Phases</h3>
                {selectedPatch.canary_phases?.map((phase, i) => (
                  <div
                    key={i}
                    className="phase-row"
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      padding: '12px',
                      backgroundColor: i % 2 === 0 ? '#f9f9f9' : 'white',
                      borderRadius: '4px',
                      marginBottom: '8px',
                    }}
                  >
                    <span style={{ fontWeight: '500' }}>
                      {phase.name}
                      {typeof phase.progress === 'number'
                        ? ` - ${phase.progress}%`
                        : ''}
                    </span>
                    <span className={`status-badge ${phase.status}`}>
                      {phase.status}
                    </span>
                  </div>
                ))}
              </div>

              <div className="detail-section">
                <h3>Affected Hosts</h3>
                {Array.isArray(selectedPatch.affected_hosts) &&
                selectedPatch.affected_hosts.length > 0 ? (
                  <ul style={{ paddingLeft: '20px', lineHeight: '1.8' }}>
                    {selectedPatch.affected_hosts.map((host, i) => (
                      <li key={i} style={{ marginBottom: '4px' }}>
                        {host}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>No specific host details available.</p>
                )}
              </div>

              <div className="detail-section">
                <h3>Health Checks</h3>
                <ul style={{ paddingLeft: '20px', lineHeight: '1.8' }}>
                  {selectedPatch.health_checks?.map((check, i) => (
                    <li key={i} style={{ marginBottom: '8px' }}>
                      {check}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

