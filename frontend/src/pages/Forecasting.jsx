import React, { useState, useEffect } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

export default function Forecasting() {
  const [chartData, setChartData] = useState({
    labels: [],
    datasets: []
  });

  useEffect(() => {
    // Generate time series data
    const hours = Array.from({length: 24}, (_, i) => `${i}:00`);
    const cpuActual = hours.map((_, i) => 40 + Math.sin(i/3) * 15 + Math.random() * 10);
    const cpuPredicted = hours.map((_, i) => 40 + Math.sin(i/3) * 15 + 5);
    const memoryActual = hours.map((_, i) => 55 + Math.cos(i/4) * 10 + Math.random() * 8);
    
    setChartData({
      labels: hours,
      datasets: [
        {
          label: 'CPU Usage (Actual)',
          data: cpuActual,
          borderColor: 'rgb(99, 102, 241)',
          backgroundColor: 'rgba(99, 102, 241, 0.1)',
          fill: true,
          tension: 0.4
        },
        {
          label: 'CPU Predicted',
          data: cpuPredicted,
          borderColor: 'rgb(239, 68, 68)',
          borderDash: [5, 5],
          fill: false,
          tension: 0.4
        },
        {
          label: 'Memory Usage',
          data: memoryActual,
          borderColor: 'rgb(16, 185, 129)',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          fill: true,
          tension: 0.4
        }
      ]
    });
  }, []);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: false
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        ticks: {
          callback: (value) => value + '%'
        }
      }
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Forecasting</h1>
      </div>

      <div className="metrics-grid-3">
        <div className="metric-card">
          <div className="metric-label">Anomaly Detection</div>
          <div className="metric-value">92%</div>
          <div className="metric-change positive">↑ Accuracy</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Risk Prediction</div>
          <div className="metric-value">87%</div>
          <div className="metric-change positive">↑ Confidence</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Patch Success</div>
          <div className="metric-value">94%</div>
          <div className="metric-change positive">↑ Rate</div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title">Risk & Capacity Trends (24h Forecast)</div>
        </div>
        <div style={{ height: '400px', padding: '20px' }}>
          <Line data={chartData} options={options} />
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title">Upcoming Risks</div>
        </div>
        <div className="risk-list">
          <div className="risk-item">
            <AlertTriangle className="risk-icon high" />
            <div className="risk-content">
              <div className="risk-title">CPU spike predicted on db-prod-01</div>
              <div className="risk-time">Expected: Tomorrow 4:15 AM • Confidence: 87%</div>
            </div>
          </div>
          <div className="risk-item">
            <AlertTriangle className="risk-icon medium" />
            <div className="risk-content">
              <div className="risk-title">Memory exhaustion on web cluster</div>
              <div className="risk-time">Expected: Oct 18, 2:30 PM • Confidence: 75%</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}