// =========================================================
// ScamShield Frontend — App Entry
// Author: Ayesha Habib
// Description: 
//   Main React component serving as the entry point
//   for ScamShield’s user interface.
// =========================================================


import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import axios from "axios";
import { Shield, History, BarChart3, AlertTriangle, CheckCircle, AlertCircle } from "lucide-react";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Badge } from "./components/ui/badge";
import { Progress } from "./components/ui/progress";
import { Separator } from "./components/ui/separator";
import { toast } from "sonner";
import { Toaster } from "./components/ui/sonner";
import "./App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Navigation Component
const Navigation = () => {
  const location = useLocation();
  
  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-2">
            <Shield className="h-8 w-8 text-blue-600" />
            <span className="text-xl font-semibold text-slate-900">ScamShield</span>
          </div>
          
          <div className="flex space-x-1">
            <Link to="/">
              <Button 
                variant={location.pathname === "/" ? "default" : "ghost"}
                className="flex items-center space-x-2"
              >
                <Shield className="h-4 w-4" />
                <span>Scanner</span>
              </Button>
            </Link>
            <Link to="/history">
              <Button 
                variant={location.pathname === "/history" ? "default" : "ghost"}
                className="flex items-center space-x-2"
              >
                <History className="h-4 w-4" />
                <span>History</span>
              </Button>
            </Link>
            <Link to="/stats">
              <Button 
                variant={location.pathname === "/stats" ? "default" : "ghost"}
                className="flex items-center space-x-2"
              >
                <BarChart3 className="h-4 w-4" />
                <span>Stats</span>
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

// Scanner Component
const Scanner = () => {
  const [content, setContent] = useState("");
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState(null);

  const handleScan = async () => {
    if (!content.trim()) {
      toast.error("Please enter content to scan");
      return;
    }

    setScanning(true);
    try {
      const response = await axios.post(`${API}/scan`, {
        content: content.trim()
      });
      setResult(response.data);
      toast.success("Scan completed successfully");
    } catch (error) {
      console.error("Scan error:", error);
      toast.error("Failed to scan content. Please try again.");
    }
    setScanning(false);
  };

  const getRiskColor = (score) => {
    if (score <= 30) return "text-green-600";
    if (score <= 70) return "text-yellow-600";
    return "text-red-600";
  };

  const getRiskIcon = (label) => {
    if (label.includes("Safe")) return <CheckCircle className="h-5 w-5 text-green-600" />;
    if (label.includes("Suspicious")) return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
    return <AlertCircle className="h-5 w-5 text-red-600" />;
  };

  const getProgressColor = (score) => {
    if (score <= 30) return "bg-green-500";
    if (score <= 70) return "bg-yellow-500";
    return "bg-red-500";
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <div className="flex justify-center mb-4">
          <div className="p-3 bg-blue-100 rounded-full">
            <Shield className="h-12 w-12 text-blue-600" />
          </div>
        </div>
        <h1 className="text-4xl font-bold text-slate-900 mb-4">
          Protect Yourself from Scams
        </h1>
        <p className="text-lg text-slate-600 max-w-2xl mx-auto">
          Paste any text message, phone number, or link below to check if it's a scam. 
          Our AI-powered system analyzes patterns to keep you safe.
        </p>
      </div>

      {/* Scanner Form */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Shield className="h-5 w-5" />
            <span>Scam Scanner</span>
          </CardTitle>
          <CardDescription>
            Enter any suspicious text message, phone number, or URL to analyze
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="content">Content to Scan</Label>
            <textarea
              id="content"
              placeholder="Paste your text message, phone number, or URL here..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="w-full min-h-[120px] p-3 border border-slate-300 rounded-md resize-y focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <Button 
            onClick={handleScan} 
            disabled={scanning || !content.trim()}
            className="w-full"
            size="lg"
          >
            {scanning ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Scanning...
              </>
            ) : (
              <>
                <Shield className="h-4 w-4 mr-2" />
                Scan Now
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              {getRiskIcon(result.label)}
              <span>Scan Results</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Risk Score */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Label>Risk Score</Label>
                <span className={`text-2xl font-bold ${getRiskColor(result.risk_score)}`}>
                  {result.risk_score}/100
                </span>
              </div>
              <div className="relative">
                <Progress 
                  value={result.risk_score} 
                  className="h-3"
                />
                <div 
                  className={`absolute top-0 left-0 h-3 rounded-full transition-all duration-500 ${getProgressColor(result.risk_score)}`}
                  style={{ width: `${result.risk_score}%` }}
                ></div>
              </div>
            </div>

            {/* Label */}
            <div className="flex items-center space-x-2">
              <Label>Status:</Label>
              <Badge 
                variant={result.label.includes("Safe") ? "default" : result.label.includes("Suspicious") ? "secondary" : "destructive"}
                className="text-sm"
              >
                {result.label}
              </Badge>
            </div>

            {/* Type */}
            <div className="flex items-center space-x-2">
              <Label>Type:</Label>
              <Badge variant="outline" className="capitalize">
                {result.scan_type}
              </Badge>
            </div>

            {/* Guidance */}
            <div className="p-4 bg-slate-50 rounded-lg">
              <Label className="text-sm font-medium text-slate-700">Guidance</Label>
              <p className="mt-1 text-slate-900">{result.guidance}</p>
            </div>

            {/* Triggers */}
            {result.triggers && result.triggers.length > 0 && (
              <div className="space-y-2">
                <Label>Detection Triggers</Label>
                <div className="flex flex-wrap gap-2">
                  {result.triggers.map((trigger, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {trigger}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Original Content */}
            <div className="space-y-2">
              <Label>Scanned Content</Label>
              <div className="p-3 bg-slate-100 rounded-md text-sm text-slate-700 break-words">
                {result.content}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// History Component
const HistoryPage = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API}/history`);
      setHistory(response.data);
    } catch (error) {
      console.error("Failed to fetch history:", error);
      toast.error("Failed to load scan history");
    }
    setLoading(false);
  };

  const getRiskIcon = (label) => {
    if (label.includes("Safe")) return <CheckCircle className="h-4 w-4 text-green-600" />;
    if (label.includes("Suspicious")) return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
    return <AlertCircle className="h-4 w-4 text-red-600" />;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Scan History</h1>
        <p className="text-slate-600">Your last 10 scans and their results</p>
      </div>

      {history.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center h-64">
            <History className="h-12 w-12 text-slate-400 mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">No scan history</h3>
            <p className="text-slate-600 text-center">
              Start scanning content to see your history here
            </p>
            <Link to="/" className="mt-4">
              <Button>Start Scanning</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {history.map((scan) => (
            <Card key={scan.id}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    {getRiskIcon(scan.label)}
                    <Badge 
                      variant={scan.label.includes("Safe") ? "default" : scan.label.includes("Suspicious") ? "secondary" : "destructive"}
                    >
                      {scan.label}
                    </Badge>
                    <Badge variant="outline" className="capitalize">
                      {scan.scan_type}
                    </Badge>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-semibold text-slate-900">
                      {scan.risk_score}/100
                    </div>
                    <div className="text-sm text-slate-500">
                      {formatDate(scan.timestamp)}
                    </div>
                  </div>
                </div>
                
                <div className="p-3 bg-slate-50 rounded-md mb-3">
                  <p className="text-sm text-slate-700 break-words">
                    {scan.content.length > 150 
                      ? `${scan.content.substring(0, 150)}...`
                      : scan.content
                    }
                  </p>
                </div>
                
                <p className="text-sm text-slate-600">{scan.guidance}</p>
                
                {scan.triggers && scan.triggers.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    {scan.triggers.map((trigger, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {trigger}
                      </Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

// Stats Component
const StatsPage = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/stats`);
      setStats(response.data);
    } catch (error) {
      console.error("Failed to fetch stats:", error);
      toast.error("Failed to load statistics");
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Statistics</h1>
        <p className="text-slate-600">Overview of scanning activity and results</p>
      </div>

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Total Scans</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-slate-900">{stats.total_scans}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-green-600">Safe</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{stats.safe_scans}</div>
              <div className="text-sm text-slate-500">
                {stats.total_scans > 0 ? Math.round((stats.safe_scans / stats.total_scans) * 100) : 0}%
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-yellow-600">Suspicious</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">{stats.suspicious_scans}</div>
              <div className="text-sm text-slate-500">
                {stats.total_scans > 0 ? Math.round((stats.suspicious_scans / stats.total_scans) * 100) : 0}%
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-red-600">Dangerous</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{stats.dangerous_scans}</div>
              <div className="text-sm text-slate-500">
                {stats.total_scans > 0 ? Math.round((stats.dangerous_scans / stats.total_scans) * 100) : 0}%
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {stats && stats.total_scans === 0 && (
        <Card className="mt-8">
          <CardContent className="flex flex-col items-center justify-center h-64">
            <BarChart3 className="h-12 w-12 text-slate-400 mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">No data available</h3>
            <p className="text-slate-600 text-center">
              Start scanning content to see statistics here
            </p>
            <Link to="/" className="mt-4">
              <Button>Start Scanning</Button>
            </Link>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// Main App Component
const App = () => {
  return (
    <div className="min-h-screen bg-slate-50">
      <BrowserRouter>
        <Navigation />
        <main>
          <Routes>
            <Route path="/" element={<Scanner />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/stats" element={<StatsPage />} />
          </Routes>
        </main>
        <Toaster />
      </BrowserRouter>
    </div>
  );
};

export default App;