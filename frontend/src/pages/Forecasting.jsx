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

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

export default function Forecasting() {
  const [chartData, setChartData] = useState({
    labels: [],
    datasets: []
  });
  const [metrics, setMetrics] = useState({
    anomaly_detection_accuracy: 0,
    risk_prediction_confidence: 0,
    patch_success_rate: 0
  });
  const [upcomingRisks, setUpcomingRisks] = useState([]);

  // PHASE 5: Fetch real forecast data from API
  const fetchForecastData = async () => {
    try {
      const res = await fetch(`${API_BASE}/forecasts`);
      const data = await res.json();

      console.log('Forecast data received:', data);

      // Update metrics
      setMetrics({
        anomaly_detection_accuracy: data.anomaly_detection_accuracy?.toFixed(1) || 0,
        risk_prediction_confidence: data.risk_prediction_confidence?.toFixed(1) || 0,
        patch_success_rate: data.patch_success_rate?.toFixed(1) || 0
      });

      // Update chart data
      if (data.metrics && data.metrics.hours) {
        setChartData({
          labels: data.metrics.hours,
          datasets: [
            {
              label: 'CPU Usage (Actual)',
              data: data.metrics.cpu.actual.map(v => parseFloat(v.toFixed(1))),
              borderColor: 'rgb(99, 102, 241)',
              backgroundColor: 'rgba(99, 102, 241, 0.1)',
              fill: true,
              tension: 0.4
            },
            {
              label: 'CPU Predicted',
              data: data.metrics.cpu.predicted.map(v => parseFloat(v.toFixed(1))),
              borderColor: 'rgb(239, 68, 68)',
              borderDash: [5, 5],
              fill: false,
              tension: 0.4
            },
            {
              label: 'Memory Usage',
              data: data.metrics.memory.actual.map(v => parseFloat(v.toFixed(1))),
              borderColor: 'rgb(16, 185, 129)',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              fill: true,
              tension: 0.4
            }
          ]
        });
      }

      // Update upcoming risks
      if (data.upcoming_risks) {
        setUpcomingRisks(data.upcoming_risks);
      }
    } catch (error) {
      console.error('Error fetching forecast data:', error);
    }
  };

  useEffect(() => {
    // Fetch on mount
    fetchForecastData();

    // PHASE 5: Set up 3-second refresh cycle (same as dashboard)
    const interval = setInterval(fetchForecastData, 3000);
    return () => clearInterval(interval);
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

      {/* PHASE 5: Real-time metrics from API */}
      <div className="metrics-grid-3">
        <div className="metric-card">
          <div className="metric-label">Anomaly Detection</div>
          <div className="metric-value">{metrics.anomaly_detection_accuracy}%</div>
          <div className="metric-change positive">↑ Accuracy</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Risk Prediction</div>
          <div className="metric-value">{metrics.risk_prediction_confidence}%</div>
          <div className="metric-change positive">↑ Confidence</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Patch Success</div>
          <div className="metric-value">{metrics.patch_success_rate}%</div>
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

      {/* PHASE 5: Real upcoming risks from API */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">Upcoming Risks</div>
        </div>
        <div className="risk-list">
          {upcomingRisks.length > 0 ? (
            upcomingRisks.map((risk, idx) => (
              <div key={idx} className="risk-item">
                <AlertTriangle className={`risk-icon ${risk.severity}`} />
                <div className="risk-content">
                  <div className="risk-title">{risk.title}</div>
                  <div className="risk-time">
                    Expected: {risk.expected_time_text} • Confidence: {risk.confidence?.toFixed(1)}%
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="risk-item">
              <div className="risk-content">
                <div className="risk-title">Loading upcoming risks...</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
