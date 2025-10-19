// =========================================================
// ScamShield Frontend — ScannerInput Component
// Author: Ayesha Habib
// Description:
//   Provides a text box for scanning suspicious messages, links,
//   or phone numbers. Communicates with the backend /scan endpoint
//   and displays the result using the RiskResult component.
// =========================================================

import React, { useState } from "react";
import CONFIG from "../config";
import RiskResult from "./RiskResult";
import "./ScannerInput.css";

export default function ScannerInput() {
  // ---------------------------------------------
  // Local component state
  // ---------------------------------------------
  const [input, setInput] = useState("");   // User’s entered text
  const [result, setResult] = useState(null); // API result data
  const [loading, setLoading] = useState(false); // Loading flag

  // ---------------------------------------------
  // Function: handleScan
  // Sends the text to the backend for analysis
  // ---------------------------------------------
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

  // ---------------------------------------------
  // Component Rendering
  // ---------------------------------------------
  return (
    <div className="scanner-container">
      <h2>🔍 ScamShield Message Scanner</h2>

      {/* Text input area */}
      <textarea
        className="scanner-textarea"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Paste suspicious message, link, or phone number..."
      />

      {/* Scan button */}
      <button onClick={handleScan} disabled={loading}>
        {loading ? "Scanning..." : "Scan Now"}
      </button>

      {/* Display result below */}
      <RiskResult result={result} />
    </div>
  );
}

