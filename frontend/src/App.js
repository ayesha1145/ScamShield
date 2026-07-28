import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navigation from "./components/Navigation";
import ScannerInput from "./components/ScannerInput";
import ScanResult from "./components/ScanResult";
import "./App.css";

function App() {
  const [scanResult, setScanResult] = useState(null);

  const handleScan = (result) => {
    setScanResult(result);
  };

  return (
    <Router>
      <div className="App">
        <Navigation />
        <main>
          <Routes>
            <Route path="/" element={
              <>
                <ScannerInput onScan={handleScan} />
                <ScanResult result={scanResult} />
              </>
            } />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
