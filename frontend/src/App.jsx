import React, { useState, useEffect, useRef } from 'react';
import {
  Activity, Search, Moon, Sun, Power,
  LayoutDashboard, AlertCircle, Wrench, TrendingUp, FileText,
  Terminal, ChevronUp, ChevronDown, Trash2
} from 'lucide-react';
import './styles/main.css';
import Dashboard from './pages/Dashboard';
import Incidents from './pages/Incidents';
import PatchManagement from './pages/PatchManagement';
import Forecasting from './pages/Forecasting';
import AuditLogs from './pages/AuditLogs';

// Use environment variable for API base, fallback to localhost for development
// In production, this should be set to the actual API Gateway URL or '/api' for same-origin
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

// Error Boundary Component to catch React errors
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary] Caught error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          backgroundColor: '#1a1a1a',
          color: 'white',
          padding: '20px',
          textAlign: 'center'
        }}>
          <AlertCircle size={64} color="#dc3545" style={{ marginBottom: '20px' }} />
          <h1 style={{ marginBottom: '10px' }}>Something went wrong</h1>
          <p style={{ color: '#888', marginBottom: '20px' }}>
            {this.state.error?.message || 'An unexpected error occurred'}
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '10px 20px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [darkMode, setDarkMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [killSwitchActive, setKillSwitchActive] = useState(false);
  const [killSwitchLoading, setKillSwitchLoading] = useState(false);
  const [simulationRunning, setSimulationRunning] = useState(false);
  const [simulationLoading, setSimulationLoading] = useState(false);
  const [logsPanelOpen, setLogsPanelOpen] = useState(false);
  const [logs, setLogs] = useState([]);
  const [logFilter, setLogFilter] = useState('ALL');
  const [terminalOutputMode, setTerminalOutputMode] = useState('full');
  const logsEndRef = useRef(null);

  useEffect(() => {
    document.body.classList.toggle('dark-mode', darkMode);
  }, [darkMode]);

  // Poll kill switch status every 2 seconds
  useEffect(() => {
    const fetchKillSwitchStatus = async () => {
      try {
        const res = await fetch(`${API_BASE}/kill-switch/status`);
        const data = await res.json();
        setKillSwitchActive(data.active);
      } catch (error) {
        console.error('Failed to fetch kill switch status:', error);
      }
    };

    fetchKillSwitchStatus();
    const interval = setInterval(fetchKillSwitchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  // Poll simulation status every 2 seconds
  useEffect(() => {
    const fetchSimulationStatus = async () => {
      try {
        const res = await fetch(`${API_BASE}/simulation/status`);
        const data = await res.json();
        setSimulationRunning(data.running);
      } catch (error) {
        console.error('Failed to fetch simulation status:', error);
      }
    };

    fetchSimulationStatus();
    const interval = setInterval(fetchSimulationStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  // Poll logs when panel is open and simulation is running
  useEffect(() => {
    if (!logsPanelOpen && !simulationRunning) return;

    const fetchLogs = async () => {
      try {
        const filterParam = logFilter !== 'ALL' ? `&log_type=${logFilter}` : '';
        const res = await fetch(`${API_BASE}/logs?limit=1000${filterParam}`);
        const data = await res.json();
        setLogs(data.logs || []);
      } catch (error) {
        console.error('Failed to fetch logs:', error);
      }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 1500);
    return () => clearInterval(interval);
  }, [logsPanelOpen, simulationRunning, logFilter]);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (logsPanelOpen && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, logsPanelOpen]);

  // Fetch terminal output mode on mount
  useEffect(() => {
    const fetchTerminalMode = async () => {
      try {
        const res = await fetch(`${API_BASE}/terminal-output-mode`);
        const data = await res.json();
        setTerminalOutputMode(data.mode);
      } catch (error) {
        console.error('Failed to fetch terminal output mode:', error);
      }
    };

    fetchTerminalMode();
  }, []);

  const handleTerminalModeChange = async (newMode) => {
    try {
      const res = await fetch(`${API_BASE}/terminal-output-mode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: newMode })
      });
      const data = await res.json();
      if (!data.error) {
        setTerminalOutputMode(newMode);
      }
    } catch (error) {
      console.error('Failed to set terminal output mode:', error);
    }
  };

  const handleKillSwitch = async () => {
    const action = killSwitchActive ? 'RESUME' : 'HALT';
    const message = killSwitchActive
      ? 'This will RESUME all autonomous agent actions. Continue?'
      : 'This will HALT ALL autonomous agent actions. Continue?';

    if (window.confirm(message)) {
      setKillSwitchLoading(true);
      try {
        const res = await fetch(`${API_BASE}/kill-switch/toggle`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        setKillSwitchActive(data.active);

        // Show confirmation
        alert(data.message);
      } catch (error) {
        console.error('Failed to toggle kill switch:', error);
        alert('Failed to toggle kill switch. Check backend connection.');
      } finally {
        setKillSwitchLoading(false);
      }
    }
  };

  const handleSimulationToggle = async () => {
    const action = simulationRunning ? 'stop' : 'start';
    const message = simulationRunning
      ? 'Stop incident generation? No new incidents will be created.'
      : 'Start incident generation? The system will create incidents every 30-60 seconds.';

    if (window.confirm(message)) {
      setSimulationLoading(true);
      try {
        const res = await fetch(`${API_BASE}/simulation/${action}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        setSimulationRunning(data.running);
        alert(data.message);
      } catch (error) {
        console.error('Failed to toggle simulation:', error);
        alert('Failed to toggle simulation. Check backend connection.');
      } finally {
        setSimulationLoading(false);
      }
    }
  };

  const clearLogs = () => {
    if (window.confirm('Clear all logs?')) {
      setLogs([]);
    }
  };

  const getLogColor = (logType) => {
    const colors = {
      'START': '#28a745',
      'STOP': '#dc3545',
      'INCIDENT': '#007bff',
      'PROCESSING': '#ffc107',
      'SUCCESS': '#28a745',
      'PATCH': '#17a2b8',
      'ACTION': '#fd7e14',
      'WARNING': '#dc3545',
      'METRICS': '#6c757d',
      'KILLSWITCH': '#dc3545',
      'INFO': '#6c757d',
      // New narrative log types
      'GENERATOR': '#9b59b6',      // Purple - incident generation
      'ORCHESTRATOR': '#e67e22',   // Orange - orchestrator decisions
      'ALERTOPS': '#3498db',       // Blue - alert correlation
      'PREDICTIVEOPS': '#1abc9c',  // Teal - predictive analysis
      'PATCHOPS': '#2ecc71',       // Green - patch operations
      'TASKOPTS': '#f39c12',       // Gold - task execution
      'LEARNING': '#8e44ad',       // Violet - learning/memory
      'PERCEPTION': '#34495e',     // Dark gray - perception
      'SYNTHESIS': '#d35400'       // Dark orange - synthesis
    };
    return colors[logType] || '#6c757d';
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard': return <Dashboard />;
      case 'incidents': return <Incidents />;
      case 'patch': return <PatchManagement />;
      case 'forecasting': return <Forecasting />;
      case 'audit': return <AuditLogs />;
      default: return <Dashboard />;
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <div className="header-title">
            <Activity size={24} />
            OpsForge AI
          </div>
          <div className="search-bar">
            <Search size={16} />
            <input 
              type="text" 
              placeholder="Search incidents, alerts, hosts..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
        <div className="header-right">
          <button className="icon-btn" onClick={() => setDarkMode(!darkMode)}>
            {darkMode ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button
            className={`kill-switch ${killSwitchActive ? 'active' : ''} ${killSwitchLoading ? 'loading' : ''}`}
            onClick={handleKillSwitch}
            disabled={killSwitchLoading}
            title={killSwitchActive ? 'Click to resume autonomous actions' : 'Click to halt all autonomous actions'}
          >
            <Power size={18} />
            {killSwitchLoading ? 'Toggling...' : (killSwitchActive ? 'ACTIVE' : 'Inactive')}
          </button>
        </div>
      </header>

      <div className="layout">
        <aside className="sidebar-nav">
          <nav>
            <div 
              className={`nav-item ${currentPage === 'dashboard' ? 'active' : ''}`}
              onClick={() => setCurrentPage('dashboard')}
            >
              <LayoutDashboard size={20} />
              <span>Dashboard</span>
            </div>
            <div 
              className={`nav-item ${currentPage === 'incidents' ? 'active' : ''}`}
              onClick={() => setCurrentPage('incidents')}
            >
              <AlertCircle size={20} />
              <span>Incidents</span>
            </div>
            <div 
              className={`nav-item ${currentPage === 'patch' ? 'active' : ''}`}
              onClick={() => setCurrentPage('patch')}
            >
              <Wrench size={20} />
              <span>Patch Management</span>
            </div>
            <div 
              className={`nav-item ${currentPage === 'forecasting' ? 'active' : ''}`}
              onClick={() => setCurrentPage('forecasting')}
            >
              <TrendingUp size={20} />
              <span>Forecasting</span>
            </div>
            <div
              className={`nav-item ${currentPage === 'audit' ? 'active' : ''}`}
              onClick={() => setCurrentPage('audit')}
            >
              <FileText size={20} />
              <span>Audit Logs</span>
            </div>
          </nav>

          <div style={{
            padding: '20px 15px',
            borderTop: '1px solid #e0e0e0',
            marginTop: 'auto'
          }}>
            <button
              onClick={handleSimulationToggle}
              disabled={simulationLoading}
              style={{
                width: '100%',
                padding: '12px 16px',
                backgroundColor: simulationRunning ? '#dc3545' : '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: simulationLoading ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                transition: 'all 0.2s',
                opacity: simulationLoading ? 0.6 : 1
              }}
            >
              {simulationLoading ? (
                <span>Processing...</span>
              ) : simulationRunning ? (
                <>
                  <span style={{ fontSize: '16px' }}>■</span>
                  <span>Stop Simulation</span>
                </>
              ) : (
                <>
                  <span style={{ fontSize: '16px' }}>▶</span>
                  <span>Start Simulation</span>
                </>
              )}
            </button>

            <div style={{
              marginTop: '12px',
              padding: '10px',
              backgroundColor: simulationRunning ? '#fff3cd' : '#d1ecf1',
              border: `1px solid ${simulationRunning ? '#ffc107' : '#bee5eb'}`,
              borderRadius: '4px',
              fontSize: '12px',
              lineHeight: '1.4',
              color: '#333'
            }}>
              {simulationRunning ? (
                <span>
                  <strong>Simulation Active:</strong> Incidents are being generated every 30-60 seconds automatically.
                </span>
              ) : (
                <span>
                  <strong>Simulation Stopped:</strong> Click "Start Simulation" to begin generating incidents for demonstration.
                </span>
              )}
            </div>
          </div>
        </aside>

        <main className="main-content">
          {killSwitchActive && (
            <div className="alert alert-danger" style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 20px',
              marginBottom: '20px',
              backgroundColor: '#dc3545',
              color: 'white',
              borderRadius: '4px',
              fontWeight: 'bold'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Power size={20} />
                <div>
                  <div>KILL SWITCH ACTIVE - All autonomous actions paused</div>
                  <div style={{ fontSize: '12px', fontWeight: 'normal', marginTop: '4px', opacity: 0.9 }}>
                    Incident generation paused • Action execution blocked • Patch deployments paused
                  </div>
                </div>
              </div>
              <button
                onClick={handleKillSwitch}
                style={{
                  padding: '6px 12px',
                  backgroundColor: 'white',
                  color: '#dc3545',
                  border: 'none',
                  borderRadius: '4px',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}
              >
                Resume Operations
              </button>
            </div>
          )}
          {renderPage()}
        </main>

        {/* Terminal Log Viewer Panel */}
        <div style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          backgroundColor: '#1e1e1e',
          borderTop: '2px solid #333',
          transition: 'transform 0.3s ease',
          transform: logsPanelOpen ? 'translateY(0)' : 'translateY(calc(100% - 40px))',
          zIndex: 1000,
          height: '350px'
        }}>
          {/* Panel Header */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '8px 16px',
            backgroundColor: '#2d2d2d',
            borderBottom: logsPanelOpen ? '1px solid #444' : 'none',
            cursor: 'pointer',
            userSelect: 'none'
          }} onClick={() => setLogsPanelOpen(!logsPanelOpen)}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#fff' }}>
              <Terminal size={18} />
              <span style={{ fontWeight: 'bold', fontSize: '14px' }}>System Logs</span>
              <span style={{
                fontSize: '12px',
                backgroundColor: simulationRunning ? '#28a745' : '#6c757d',
                padding: '2px 8px',
                borderRadius: '3px'
              }}>
                {simulationRunning ? 'ACTIVE' : 'IDLE'}
              </span>
              <span style={{ fontSize: '12px', color: '#888' }}>
                {logs.length} entries
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              {logsPanelOpen && (
                <>
                  <select
                    value={terminalOutputMode}
                    onClick={(e) => e.stopPropagation()}
                    onChange={(e) => { e.stopPropagation(); handleTerminalModeChange(e.target.value); }}
                    style={{
                      padding: '4px 8px',
                      backgroundColor: '#3d3d3d',
                      color: 'white',
                      border: '1px solid #555',
                      borderRadius: '3px',
                      fontSize: '12px',
                      cursor: 'pointer',
                      textTransform: 'uppercase'
                    }}
                  >
                    <option value="full">FULL</option>
                    <option value="selective">SELECTIVE</option>
                    <option value="none">NONE</option>
                  </select>
                  <select
                    value={logFilter}
                    onClick={(e) => e.stopPropagation()}
                    onChange={(e) => { e.stopPropagation(); setLogFilter(e.target.value); }}
                    style={{
                      padding: '4px 8px',
                      backgroundColor: '#3d3d3d',
                      color: 'white',
                      border: '1px solid #555',
                      borderRadius: '3px',
                      fontSize: '12px',
                      cursor: 'pointer'
                    }}
                  >
                    <option value="ALL">All Logs</option>
                    <option value="INCIDENT">Incidents</option>
                    <option value="ALERTOPS">AlertOps</option>
                    <option value="PREDICTIVEOPS">PredictiveOps</option>
                    <option value="PATCHOPS">PatchOps</option>
                    <option value="TASKOPS">TaskOps</option>
                    <option value="ORCHESTRATOR">Orchestrator</option>
                    <option value="SYNTHESIS">Synthesis</option>
                    <option value="METRICS">Metrics</option>
                    <option value="GENERATOR">Generator</option>
                    <option value="SUCCESS">Success</option>
                    <option value="ERROR">Errors</option>
                  </select>
                  <button
                    onClick={(e) => { e.stopPropagation(); clearLogs(); }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '4px 10px',
                      backgroundColor: '#dc3545',
                      color: 'white',
                      border: 'none',
                      borderRadius: '3px',
                      fontSize: '12px',
                      cursor: 'pointer'
                    }}
                  >
                    <Trash2 size={14} />
                    Clear
                  </button>
                </>
              )}
              {logsPanelOpen ? <ChevronDown size={18} color="#fff" /> : <ChevronUp size={18} color="#fff" />}
            </div>
          </div>

          {/* Panel Content */}
          {logsPanelOpen && (
            <div style={{
              height: 'calc(100% - 41px)',
              overflowY: 'auto',
              padding: '12px',
              fontFamily: 'monospace',
              fontSize: '13px',
              color: '#d4d4d4',
              backgroundColor: '#1e1e1e'
            }}>
              {logs.length === 0 ? (
                <div style={{ textAlign: 'center', color: '#888', padding: '20px' }}>
                  No logs yet. Start simulation to see activity.
                </div>
              ) : (
                logs.map((log, idx) => (
                  <div key={idx} style={{
                    display: 'flex',
                    gap: '12px',
                    marginBottom: '4px',
                    lineHeight: '1.6'
                  }}>
                    <span style={{ color: '#888', minWidth: '70px' }}>
                      {log.timestamp}
                    </span>
                    <span style={{
                      color: getLogColor(log.type),
                      fontWeight: 'bold',
                      minWidth: '100px'
                    }}>
                      [{log.type}]
                    </span>
                    <span style={{ color: '#d4d4d4', flex: 1 }}>
                      {log.message}
                    </span>
                  </div>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Wrap App with ErrorBoundary to catch and display errors gracefully
export default function AppWithErrorBoundary() {
  return (
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  );
}
