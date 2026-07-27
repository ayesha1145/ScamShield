// ==========================================
// ScamShield Frontend — Scan Results
// Author: Ayesha Habib
// Description:
// Displays scan results with risk level,
// highlights suspicious content, and keeps
// a consistent look with the app theme.
// ==========================================

import React from "react";
import "./ScanResult.css";

export default function ScanResult({ result }) {
  if (!result)
    return (
      <div className="result-placeholder">
        <p>🔎 Scan a message to see results here.</p>
      </div>
    );

  const { riskLevel, message, suggestions } = result;

  return (
    <div className="result-card">
      <h2 className={`risk-title ${riskLevel.toLowerCase()}`}>
        Risk Level: {riskLevel}
      </h2>

      <div className="message-box">
        <p>{message}</p>
      </div>

      {suggestions?.length > 0 && (
        <ul className="suggestion-list">
          {suggestions.map((tip, index) => (
            <li key={index}>⚠️ {tip}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

