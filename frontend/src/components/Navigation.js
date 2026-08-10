import React from "react";
import { Link, useLocation } from "react-router-dom";
import "./Navigation.css";

export default function Navigation() {
  const location = useLocation();

  const links = [
    { to: "/", label: "Scanner" },
    { to: "/history", label: "History" },
    { to: "/stats", label: "Stats" },
  ];

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <div className="navbar-brand">
          <span className="navbar-shield">🛡️</span>
          <span className="navbar-title">ScamShield</span>
          <span className="navbar-tag">AI-Powered</span>
        </div>
        <div className="navbar-links">
          {links.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={`nav-link ${location.pathname === to ? "active" : ""}`}
            >
              {label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
