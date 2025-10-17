import React, { useState, useEffect } from 'react';
import { 
  Activity, Search, Moon, Sun, Power, 
  LayoutDashboard, AlertCircle, Wrench, TrendingUp, FileText 
} from 'lucide-react';
import './styles/main.css';
import Dashboard from './pages/Dashboard';
import Incidents from './pages/Incidents';
import PatchManagement from './pages/PatchManagement';
import Forecasting from './pages/Forecasting';
import AuditLogs from './pages/AuditLogs';

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [darkMode, setDarkMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [killSwitchActive, setKillSwitchActive] = useState(false);

  useEffect(() => {
    document.body.classList.toggle('dark-mode', darkMode);
  }, [darkMode]);

  const handleKillSwitch = () => {
    if (window.confirm('This will halt ALL autonomous agent actions. Continue?')) {
      setKillSwitchActive(!killSwitchActive);
    }
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
            className={`kill-switch ${killSwitchActive ? 'active' : ''}`}
            onClick={handleKillSwitch}
          >
            <Power size={18} />
            Kill Switch
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
        </aside>

        <main className="main-content">
          {killSwitchActive && (
            <div className="alert alert-danger">
              KILL SWITCH ACTIVE - All autonomous actions paused
            </div>
          )}
          {renderPage()}
        </main>
      </div>
    </div>
  );
}

export default App;
