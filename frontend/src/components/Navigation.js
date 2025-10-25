// ==========================================
// ScamShield Frontend — Navigation Bar
// Author: Ayesha Habib
// Description: Provides a consistent navigation bar with links
//              to main ScamShield pages (Scanner, History, Stats).
// ==========================================

import React from "react";
import { Link, useLocation } from "react-router-dom";
import "./Navigation.css";

export default function Navigation() {
  const location = useLocation();

  return (
    <nav className="navbar">
      <h1 className="navbar-title">🛡️ ScamShield</h1>
      <div className="navbar-links">
        <Link
          to="/"
          className={location.pathname === "/" ? "active" : ""}
        >
          Scanner
        </Link>
        <Link
          to="/history"
          className={location.pathname === "/history" ? "active" : ""}
        >
          History
        </Link>
        <Link
          to="/stats"
          className={location.pathname === "/stats" ? "active" : ""}
        >
          Stats
        </Link>
      </div>
    </nav>
  );
}

