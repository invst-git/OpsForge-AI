import React, { useState, useEffect } from 'react';
import { CheckCircle, Clock, XCircle, AlertCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

export default function PatchManagement() {
  const [patches, setPatches] = useState([]);
  const [selectedPatch, setSelectedPatch] = useState(null);

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
  const patchedCount = patches.filter(p => p.status === 'completed').reduce((sum, p) => sum + p.systems, 0);
  const pendingCount = patches.filter(p => p.status === 'pending').length;
  const failedCount = patches.filter(p => p.status === 'failed').length;

  return (
    <div className="page-container">
      <h1 className="page-title">Patch Management</h1>

      <div className="metrics-grid-4">
        <div className="metric-card">
          <div className="metric-label">Total Systems</div>
          <div className="metric-value">{totalSystems}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Patched</div>
          <div className="metric-value success">{patchedCount}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Pending</div>
          <div className="metric-value warning">{pendingCount}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Failed</div>
          <div className="metric-value danger">{failedCount}</div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title">Patch Plans</div>
        </div>
        <div className="patch-list">
          {patches.map(patch => (
            <div key={patch.id} className="patch-item" onClick={() => viewPatchDetail(patch.id)}>
              <div className="patch-info">
                <div className="patch-id-name">
                  <span className="patch-id">{patch.id}</span>
                  <span className="patch-name">{patch.name}</span>
                </div>
                <div className="patch-meta">
                  <span>{patch.systems} systems</span>
                  <span>•</span>
                  <span className={`status-badge ${patch.status}`}>{patch.status.replace('_', ' ')}</span>
                </div>
              </div>
              <div className="patch-progress">
                <div className="progress-bar">
                  <div className="progress-fill" style={{width: `${patch.progress}%`}}></div>
                </div>
                <span className="progress-text">{patch.progress}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {selectedPatch && (
        <div className="modal-overlay" onClick={() => setSelectedPatch(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{selectedPatch.name}</h2>
              <button onClick={() => setSelectedPatch(null)}>×</button>
            </div>
            <div className="modal-body">
              <h3>Canary Phases</h3>
              {selectedPatch.canary_phases?.map((phase, i) => (
                <div key={i} className="phase-row">
                  <span>Phase {phase.phase}: {phase.hosts} hosts</span>
                  <span className={`status-badge ${phase.status}`}>{phase.status}</span>
                </div>
              ))}
              <h3>Health Checks</h3>
              <ul>
                {selectedPatch.health_checks?.map((check, i) => (
                  <li key={i}>{check}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}