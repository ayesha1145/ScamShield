// ===============================================
// ScamShield Frontend — Scanner Input
// Author: Ayesha Habib
// Description:
// Handles user text input and triggers AI-based risk detection.
// ===============================================

import React, { useState } from "react";
import axios from "axios";
import "./ScannerInput.css";

export default function ScannerInput({ onScan }) {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Send request to backend
      const res = await axios.post("http://127.0.0.1:8000/scan", { text: message });
      onScan(res.data); // Send data up to App.js
    } catch (error) {
      console.error("Error scanning message:", error);
      onScan(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="scanner-container">
      <form onSubmit={handleSubmit}>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Paste or type message here..."
          rows="5"
        />
        <button type="submit" disabled={loading}>
          {loading ? "Scanning..." : "Scan Message"}
        </button>
      </form>
    </div>
  );
}

