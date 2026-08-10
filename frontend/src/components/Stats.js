import React, { useEffect, useState } from "react";
import CONFIG from "../config";
import "./Stats.css";

export default function Stats() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/stats`);
        if (!response.ok) throw new Error("Failed to fetch");
        const data = await response.json();
        setStats(data);
      } catch (err) {
        setError("Unable to load statistics.");
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) return (
    <div className="stats-page">
      <div className="loading-state">
        <div className="spinner-lg" />
        <p>Loading statistics...</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="stats-page">
      <div className="error-banner">⚠️ {error}</div>
    </div>
  );

  const { total_scans, safe_scans, suspicious_scans, dangerous_scans } = stats;

  const safePercent = total_scans ? Math.round((safe_scans / total_scans) * 100) : 0;
  const suspiciousPercent = total_scans ? Math.round((suspicious_scans / total_scans) * 100) : 0;
  const dangerousPercent = total_scans ? Math.round((dangerous_scans / total_scans) * 100) : 0;

  return (
    <div className="stats-page">
      <h1 className="page-title">Statistics</h1>
      <p className="page-subtitle">Aggregate data across all scans</p>

      {total_scans === 0 ? (
        <div className="empty-state">
          <div className="icon">📊</div>
          <p>No scans yet. Run your first scan to see statistics here.</p>
        </div>
      ) : (
        <>
          {/* Total scans hero */}
          <div className="card stats-hero-card">
            <div className="stats-hero-number">{total_scans}</div>
            <div className="stats-hero-label">Total Scans Analyzed</div>
            <div className="stats-hero-sub">
              ScamShield has protected users from {dangerous_scans} dangerous threat{dangerous_scans !== 1 ? "s" : ""}
            </div>
          </div>

          {/* Breakdown cards */}
          <div className="stats-grid">
            <div className="card stat-card safe">
              <div className="stat-icon">✅</div>
              <div className="stat-number">{safe_scans}</div>
              <div className="stat-label">Safe</div>
              <div className="stat-bar">
                <div className="stat-bar-fill safe" style={{ width: `${safePercent}%` }} />
              </div>
              <div className="stat-percent">{safePercent}%</div>
            </div>

            <div className="card stat-card suspicious">
              <div className="stat-icon">⚠️</div>
              <div className="stat-number">{suspicious_scans}</div>
              <div className="stat-label">Suspicious</div>
              <div className="stat-bar">
                <div className="stat-bar-fill suspicious" style={{ width: `${suspiciousPercent}%` }} />
              </div>
              <div className="stat-percent">{suspiciousPercent}%</div>
            </div>

            <div className="card stat-card dangerous">
              <div className="stat-icon">🚨</div>
              <div className="stat-number">{dangerous_scans}</div>
              <div className="stat-label">Dangerous</div>
              <div className="stat-bar">
                <div className="stat-bar-fill dangerous" style={{ width: `${dangerousPercent}%` }} />
              </div>
              <div className="stat-percent">{dangerousPercent}%</div>
            </div>
          </div>

          {/* Model info */}
          <div className="card model-card">
            <div className="model-title">🤖 AI Model Performance</div>
            <div className="model-stats">
              <div className="model-stat">
                <div className="model-stat-value">97.2%</div>
                <div className="model-stat-label">Test Accuracy</div>
              </div>
              <div className="model-stat">
                <div className="model-stat-value">5,574</div>
                <div className="model-stat-label">Training Messages</div>
              </div>
              <div className="model-stat">
                <div className="model-stat-value">3</div>
                <div className="model-stat-label">Detection Layers</div>
              </div>
              <div className="model-stat">
                <div className="model-stat-value">&lt;200ms</div>
                <div className="model-stat-label">Avg Response Time</div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
