// =========================================================
// ScamShield Frontend — ScannerInput Component
// Author: Ayesha Habib
// Description:
//   Provides a text area for users to paste messages or links,
//   and triggers a scan request to the backend API.
// =========================================================

import React, { useState } from "react";
import CONFIG from "../config";
import "./ScannerInput.css";

export default function ScannerInput() {
  const [input, setInput] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleScan = async () => {
    if (!input.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const response = await fetch(`${CONFIG.API_BASE_URL}/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: input }),
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Scan failed:", error);
      setResult({ label: "Error", guidance: "Unable to complete scan." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="scanner-container">
      <h2>🔍 ScamShield Message Scanner</h2>
      <textarea
        className="scanner-textarea"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Paste suspicious message, link, or phone number..."
      />
      <button onClick={handleScan} disabled={loading}>
        {loading ? "Scanning..." : "Scan Now"}
      </button>

      {result && (
        <div className="scan-result card">
          <h3>Result: {result.label}</h3>
          <p>{result.guidance}</p>
        </div>
      )}
    </div>
  );
}


