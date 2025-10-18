// =========================================================
// ScamShield Frontend — Index
// Purpose:
//   Initializes the React application and renders
//   the App component into the root DOM node.
// =========================================================

import "./theme.css";

import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
