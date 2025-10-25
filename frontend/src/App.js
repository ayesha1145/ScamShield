// ===============================================
// ScamShield Frontend — App Entry Point
// Author: Ayesha Habib
// Description:
// Integrates ScannerInput and ScanResult components
// and handles live risk analysis updates.
// ===============================================

import React, { useState } from "react";
import Navigation from "./components/Navigation";
import ScannerInput from "./components/ScannerInput";
import ScanResult from "./components/ScanResult";
import "./App.css";

function App() {
  const [scanResult, setScanResult] = useState(null);

  // This function will be passed to ScannerInput
  const handleScan = (result) => {
    setScanResult(result);
  };

  return (
    <div className="App">
      <Navigation />
      <main>
        <ScannerInput onScan={handleScan} />
        <ScanResult result={scanResult} />
      </main>
    </div>
  );
}

export default App;

