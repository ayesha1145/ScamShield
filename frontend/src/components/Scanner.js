import React, { useState, useRef } from "react";
import CONFIG from "../config";
import "./Scanner.css";

const TABS = [
  { id: "text", label: "💬 Message", placeholder: "Paste a suspicious SMS or text message..." },
  { id: "url", label: "🔗 URL", placeholder: "Paste a suspicious link or website URL..." },
  { id: "phone", label: "📞 Phone", placeholder: "Enter a suspicious phone number..." },
  { id: "email", label: "📧 Email", placeholder: "Paste the full email content here (subject + body)..." },
];

const EXAMPLES = {
  text: "URGENT: Your account will be suspended in 24 hours. Click here to verify immediately!",
  url: "http://192.168.1.1/secure-bank-verify/login?user=admin",
  phone: "1-900-555-0123",
  email: "Subject: Your account has been compromised\n\nDear Customer,\n\nWe have detected unusual activity on your account. Please confirm your identity by clicking the link below and entering your banking details immediately to avoid suspension.\n\nClick here: bit.ly/secure-verify\n\nRegards,\nBank Security Team",
};

export default function Scanner() {
  const [activeTab, setActiveTab] = useState("text");
  const [input, setInput] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    setInput("");
    setResult(null);
    setError(null);
    setUploadedFile(null);
  };

  const handleScan = async () => {
    if (!input.trim() && !uploadedFile) return;
    setLoading(true);
    setResult(null);
    setError(null);

    try {
      let response;

      if (uploadedFile) {
        // File upload scan
        const formData = new FormData();
        formData.append("file", uploadedFile);
        response = await fetch(`${CONFIG.API_BASE_URL}/scan/file`, {
          method: "POST",
          body: formData,
        });
      } else {
        // Text scan
        response = await fetch(`${CONFIG.API_BASE_URL}/scan`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content: input, scan_type: activeTab }),
        });
      }

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Scan failed");
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message || "Unable to complete scan. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (file) => {
    const allowed = ['.txt', '.eml', '.csv', '.msg'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowed.includes(ext)) {
      setError(`Unsupported file type. Allowed: ${allowed.join(', ')}`);
      return;
    }
    setUploadedFile(file);
    setInput("");
    setError(null);
  };

  const handleFileDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileUpload(file);
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

  const currentTab = TABS.find(t => t.id === activeTab);
  const canScan = (input.trim() || uploadedFile) && !loading;

  return (
    <div className="scanner-page">
      {/* Hero */}
      <div className="scanner-hero">
        <h1 className="scanner-heading">
          Detect scams <span className="accent">instantly.</span>
        </h1>
        <p className="scanner-subheading">
          Analyze suspicious messages, URLs, phone numbers, emails, or uploaded files 
          through our three-layer AI detection engine.
        </p>
      </div>

      {/* Input card */}
      <div className="card scanner-card">
        {/* Tabs */}
        <div className="tabs-row">
          {TABS.map(tab => (
            <button
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => handleTabChange(tab.id)}
            >
              {tab.label}
            </button>
          ))}
          <button
            className={`tab-btn ${activeTab === "file" ? "active" : ""}`}
            onClick={() => handleTabChange("file")}
          >
            📁 File Upload
          </button>
        </div>

        {/* File upload tab */}
        {activeTab === "file" ? (
          <div
            className={`drop-zone ${dragOver ? "drag-over" : ""} ${uploadedFile ? "has-file" : ""}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleFileDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.eml,.csv,.msg"
              style={{ display: "none" }}
              onChange={(e) => e.target.files[0] && handleFileUpload(e.target.files[0])}
            />
            {uploadedFile ? (
              <div className="file-selected">
                <span className="file-icon">📄</span>
                <div>
                  <div className="file-name">{uploadedFile.name}</div>
                  <div className="file-size">{(uploadedFile.size / 1024).toFixed(1)} KB</div>
                </div>
                <button
                  className="file-remove"
                  onClick={(e) => { e.stopPropagation(); setUploadedFile(null); }}
                >
                  ✕
                </button>
              </div>
            ) : (
              <div className="drop-zone-content">
                <div className="drop-icon">📁</div>
                <div className="drop-title">Drop a file here or click to upload</div>
                <div className="drop-subtitle">Supports .txt, .eml, .csv, .msg — max 1MB</div>
              </div>
            )}
          </div>
        ) : (
          <>
            <textarea
              className="scanner-textarea"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={currentTab?.placeholder}
              rows={activeTab === "email" ? 8 : 4}
            />
            <div className="examples-row">
              <span className="examples-label">Try an example:</span>
              <button
                className="example-btn"
                onClick={() => setInput(EXAMPLES[activeTab] || "")}
              >
                Load example
              </button>
            </div>
          </>
        )}

        <button
          className="scan-btn"
          onClick={handleScan}
          disabled={!canScan}
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
      {error && <div className="error-banner">⚠️ {error}</div>}

      {/* Result */}
      {result && (
        <div className={`card result-card ${getRiskColor(result.label)}`}>
          <div className="result-header">
            <span className="result-icon">{getRiskIcon(result.label)}</span>
            <div>
              <div className="result-label">{result.label}</div>
              <div className="result-type">
                Detected as: <strong>{result.scan_type?.toUpperCase()}</strong>
              </div>
            </div>
            <div className="risk-score-circle">
              <span className="risk-score-number">{result.risk_score}</span>
              <span className="risk-score-label">/ 100</span>
            </div>
          </div>

          <p className="result-guidance">{result.guidance}</p>

          {result.explanation && result.explanation !== "No specific scam patterns detected." && (
            <div className="explanation-section">
              <div className="explanation-title">Why was this flagged?</div>
              <p className="explanation-text">{result.explanation}</p>
            </div>
          )}

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
            <div className="step-desc">Pattern matching against 30+ known scam signatures across 7 categories</div>
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
