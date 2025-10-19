// =========================================================
// ScamShield Frontend — RiskResult Component
// Author: Ayesha Habib
// Description:
//   Displays the scam detection result with color-coded labels.
// =========================================================

import React from "react";
import "./RiskResult.css";

export default function RiskResult({ result }) {
  if (!result) return null;

  const { label, guidance } = result;

  const getColorClass = (label) => {
    if (label?.toLowerCase().includes("safe")) return "safe";
    if (label?.toLowerCase().includes("suspicious")) return "suspicious";
    return "dangerous";
  };

  return (
    <div className={`risk-result card ${getColorClass(label)}`}>
      <h3>Result: {label}</h3>
      <p>{guidance}</p>
    </div>
  );
}

