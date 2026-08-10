import React, { useState } from "react";
import CONFIG from "../config";
import "./Scanner.css";

const EXAMPLES = [
  "URGENT: Your account will be suspended in 24 hours. Click here to verify!",
  "Congratulations! You've won $1,000,000. Claim your prize now at bit.ly/win",
  "Hi, this is a reminder about your appointment tomorrow at 2 PM.",
];

export default function Scanner() {
  const [input, setInput] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleScan = async () => {
    if (!input.trim()) return;
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const response = await fetch(`${CONFIG.API_BASE_URL}/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: input }),
      });
      if (!response.ok) throw new Error("Scan failed");
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError("Unable to complete scan. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (label) => {
    if (!label) return "";
    if (label.includes("Safe")) return "safe";
    if (label.includes("Suspicious")) return "suspicious";
    return "dangerous";
  };

  const getRiskIcon = (label) => {
    if (!label) return "";
    if (label.includes("Safe")) return "✅";
    if (label.includes("Suspicious")) return "⚠️";
    return "🚨";
  };

  return (
    <div className="scanner-page">
      {/* Hero */}
      <div className="scanner-hero">
        <h1 className="scanner-heading">
          Detect scams <span className="accent">instantly.</span>
        </h1>
        <p className="scanner-subheading">
          Paste any message, URL, or phone number. Our three-layer AI engine
          analyzes it in real time.
        </p>
      </div>

      {/* Input card */}
      <div className="card scanner-card">
        <div className="scanner-type-row">
          <span className="scanner-label">Content to scan</span>
        </div>
        <textarea
          className="scanner-textarea"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Paste a suspicious message, URL, or phone number..."
          rows={5}
        />

        {/* Examples */}
        <div className="examples-row">
          <span className="examples-label">Try an example:</span>
          {EXAMPLES.map((ex, i) => (
            <button
              key={i}
              className="example-btn"
              onClick={() => setInput(ex)}
            >
              Example {i + 1}
            </button>
          ))}
        </div>

        <button
          className="scan-btn"
          onClick={handleScan}
          disabled={loading || !input.trim()}
        >
          {loading ? (
            <span className="loading-row">
              <span className="spinner" /> Analyzing...
            </span>
          ) : (
            "🔍 Scan Now"
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="error-banner">⚠️ {error}</div>
      )}

      {/* Result */}
      {result && (
        <div className={`card result-card ${getRiskColor(result.label)}`}>
          <div className="result-header">
            <span className="result-icon">{getRiskIcon(result.label)}</span>
            <div>
              <div className="result-label">{result.label}</div>
              <div className="result-type">
                Detected as:{" "}
                <strong>{result.scan_type?.toUpperCase()}</strong>
              </div>
            </div>
            <div className="risk-score-circle">
              <span className="risk-score-number">{result.risk_score}</span>
              <span className="risk-score-label">/ 100</span>
            </div>
          </div>

          <p className="result-guidance">{result.guidance}</p>

          {result.triggers?.length > 0 && (
            <div className="triggers-section">
              <div className="triggers-title">Detection signals</div>
              <div className="triggers-list">
                {result.triggers.map((t, i) => (
                  <span key={i} className="trigger-tag">{t}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* How it works */}
      <div className="how-it-works">
        <div className="how-title">How ScamShield works</div>
        <div className="how-steps">
          <div className="how-step">
            <div className="step-num">01</div>
            <div className="step-name">Rule Engine</div>
            <div className="step-desc">Pattern matching against 30+ known scam signatures</div>
          </div>
          <div className="how-step">
            <div className="step-num">02</div>
            <div className="step-name">Blacklist Check</div>
            <div className="step-desc">Cross-references known scam numbers, domains, and phrases</div>
          </div>
          <div className="how-step">
            <div className="step-num">03</div>
            <div className="step-name">AI Layer</div>
            <div className="step-desc">ML model trained on 5,574 real SMS messages — 97.2% accuracy</div>
          </div>
        </div>
      </div>
    </div>
  );
}
