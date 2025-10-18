// =========================================================
// ScamShield Frontend — Config Helper
// Description:
//   Loads environment variables for app-wide use.
// =========================================================

const CONFIG = {
  API_BASE_URL: process.env.REACT_APP_API_BASE_URL || "http://localhost:8000",
  DEFAULT_LANG: process.env.REACT_APP_DEFAULT_LANG || "en",
  AI_ENABLED: process.env.REACT_APP_AI_ENABLED === "true",
};

export default CONFIG;

