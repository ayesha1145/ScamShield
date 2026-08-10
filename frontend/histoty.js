import React, { useEffect, useState } from "react";
import CONFIG from "../config";
import "./History.css";

export default function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/history`);
        if (!response.ok) throw new Error("Failed to fetch");
        const data = await response.json();
        setHistory(data);
      } catch (err) {
        setError("Unable to load scan history.");
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  const getRiskColor = (label) => {
    if (!label) return "muted";
    if (label.includes("Safe")) return "safe";
    if (label.includes("Suspicious")) return "suspicious";
    return "dangerous";
  };

  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) return (
    <div className="history-page">
      <div className="loading-state">
        <div className="spinner-lg" />
        <p>Loading scan history...</p>
      </div>
    </div>
  );

  return (
    <div className="history-page">
      <h1 className="page-title">Scan History</h1>
      <p className="page-subtitle">Your last 10 scans</p>

      {error && (
        <div className="error-banner">⚠️ {error}</div>
      )}

      {!error && history.length === 0 && (
        <div className="empty-state">
          <div className="icon">🔍</div>
          <p>No scans yet. Go to the Scanner to analyze your first message.</p>
        </div>
      )}

      <div className="history-list">
        {history.map((item) => (
          <div key={item.id} className={`card history-item ${getRiskColor(item.label)}`}>
            <div className="history-item-header">
              <span className={`history-badge ${getRiskColor(item.label)}`}>
                {item.label}
              </span>
              <span className="history-score">Risk: {item.risk_score}/100</span>
              <span className="history-date">{formatDate(item.timestamp)}</span>
            </div>
            <p className="history-content">{item.content}</p>
            <div className="history-meta">
              <span className="history-type">{item.scan_type?.toUpperCase()}</span>
              {item.triggers?.length > 0 && (
                <span className="history-triggers">
                  {item.triggers.length} signal{item.triggers.length !== 1 ? "s" : ""} detected
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
