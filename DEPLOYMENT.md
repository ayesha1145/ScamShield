# ScamShield Deployment Guide 🚀

This guide provides comprehensive instructions for deploying ScamShield locally and on Cloud.

## 📋 Prerequisites

### System Requirements
- **Operating System**: Linux/macOS/Windows with WSL2
- **Node.js**: Version 18.0 or higher
- **Python**: Version 3.11 or higher  
- **MongoDB**: Version 5.0 or higher
- **Memory**: Minimum 2GB RAM (4GB recommended)
- **Storage**: 1GB free disk space

### Required Tools
```bash
# Verify installations
node --version    # Should be 18+
python --version  # Should be 3.11+  
mongod --version  # Should be 5.0+
yarn --version    # Package manager
```

## 🏠 Local Development Setup

### 1. Repository Setup

```bash
# Clone the repository
git clone <repository-url>
cd scamshield

# Verify project structure
ls -la
# Expected: backend/ frontend/ README.md DEPLOYMENT.md
```

### 2. MongoDB Setup

#### Option A: Local MongoDB Installation
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mongodb

# macOS with Homebrew
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB service
sudo systemctl start mongod    # Linux
brew services start mongodb/brew/mongodb-community  # macOS

# Verify MongoDB is running
mongo --eval "db.adminCommand('ismaster')"
```

#### Option B: MongoDB Docker Container
```bash
# Run MongoDB in Docker
docker run --name scamshield-mongo \
  -p 27017:27017 \
  -d mongo:5.0

# Verify container is running
docker ps | grep scamshield-mongo
```

### 3. Backend Deployment

```bash
cd backend

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

**Edit `.env` file:**
```bash
MONGO_URL="mongodb://localhost:27017"
DB_NAME="scamshield_db"
CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
```

```bash
# Start the backend server
uvicorn server:app --reload --host 0.0.0.0 --port 8001

# Verify backend is running
curl http://localhost:8001/api/health
# Expected: {"status": "healthy", "ml_model_loaded": true}
```

### 4. Frontend Deployment

```bash
cd frontend

# Install dependencies
yarn install

# Configure environment variables  
cp .env.example .env
```

**Edit `.env` file:**
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
```

```bash
# Start the frontend development server
yarn start

# Application will open at http://localhost:3000
```

### 5. Verification

#### Health Checks
```bash
# Backend API health
curl http://localhost:8001/api/health

# Test scanning endpoint
curl -X POST http://localhost:8001/api/scan \
  -H "Content-Type: application/json" \
  -d '{"content":"Test message"}'

# Frontend accessibility
curl http://localhost:3000
```

## ☁️  Cloud Deployment

### 1. Platform Overview

** Cloud** provides a fully-managed container platform optimized for full-stack applications with:
- Automatic MongoDB provisioning
- Built-in load balancing
- SSL certificate management
- GitHub integration
- Zero-downtime deployments

### 2. Account Setup

```bash
# Create  account at https://cloud.example.com
# Navigate to dashboard
# Click "New Project"
```

### 3. Project Configuration

#### A. Connect Repository
1. **GitHub Integration**: Connect your ScamShield repository
2. **Branch Selection**: Choose main/master branch for deployment
3. **Auto-Deploy**: Enable automatic deployments on push

#### B. Environment Configuration
```yaml
# .yaml (automatically detected)
name: scamshield
services:
  backend:
    type: python
    version: "3.11"
    port: 8001
    build:
      command: "pip install -r requirements.txt"
    start:
      command: "uvicorn server:app --host 0.0.0.0 --port 8001"
    env:
      MONGO_URL: "${_MONGO_URL}"
      DB_NAME: "scamshield_production"

  frontend:
    type: node
    version: "18"
    port: 3000
    build:
      command: "yarn install && yarn build"
    start:
      command: "yarn start"
    env:
      REACT_APP_BACKEND_URL: "${BACKEND_URL}"

databases:
  - type: mongodb
    name: scamshield-db
```

### 4. Deployment Process

#### Step 1: Push to Repository
```bash
# Commit your changes
git add .
git commit -m "Deploy to  Cloud"
git push origin main
```

#### Step 2: Monitor Deployment
```bash
#  CLI (optional)
npm install -g @/cli
 login
 deploy --watch

# Or monitor via web dashboard
# https://dashboard..sh/projects/scamshield
```

#### Step 3: Environment Variables
Configure in  Dashboard:
```bash
# Backend Environment
MONGO_URL=<auto-provided-by->
DB_NAME=scamshield_production
CORS_ORIGINS=<auto-configured>

# Frontend Environment  
REACT_APP_BACKEND_URL=<auto-configured-backend-url>
```

### 5. Domain Configuration

#### Custom Domain Setup
```bash
# In  Dashboard:
# 1. Navigate to "Domains"
# 2. Add custom domain: scamshield.yourdomain.com
# 3. Configure DNS records as instructed
# 4. SSL certificate auto-provisioned
```

#### Default Deployment URLs
```bash
# Automatically provided:
Frontend: https://scamshield-<id>.preview.cloud.example.com
Backend:  https://scamshield-<id>.preview.cloud.example.com/api
```

## 🔧 Production Configuration

### Environment Optimization

#### Backend Production Settings
```python
# server.py adjustments for production
import logging

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/scamshield.log'),
        logging.StreamHandler()
    ]
)

# Database connection with connection pooling
client = AsyncIOMotorClient(
    mongo_url,
    maxPoolSize=10,
    minPoolSize=1,
    maxIdleTimeMS=30000
)
```

#### Frontend Production Build
```bash
# Optimize for production
yarn build

# Serve with optimizations
npm install -g serve
serve -s build -l 3000
```

### Security Configuration

#### CORS Configuration
```python
# Restrict CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[
        "https://scamshield.yourdomain.com",
        "https://scamshield-prod.cloud.example.com"
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
```

#### Rate Limiting
```python
# Add rate limiting (install slowapi)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@limiter.limit("10/minute")
@api_router.post("/scan")
async def scan_content(request: Request, scan_request: ScanRequest):
    # Existing scan logic
```

## 📊 Monitoring & Maintenance

### Health Monitoring
```bash
# Set up health check endpoints
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "ml_model_loaded": ml_model is not None,
        "database_connected": await check_db_connection(),
        "timestamp": datetime.now(timezone.utc)
    }
```

### Log Management
```bash
# Production logging
tail -f /var/log/scamshield.log

#  Cloud logs
 logs --service backend --follow
 logs --service frontend --follow
```

### Database Maintenance
```bash
# Regular database optimization
db.scan_history.createIndex({"timestamp": -1})
db.scan_history.createIndex({"risk_score": -1})

# Cleanup old scan history (keep last 30 days)
db.scan_history.deleteMany({
  "timestamp": {
    $lt: new Date(Date.now() - 30*24*60*60*1000)
  }
})
```

## 🚨 Troubleshooting

### Common Issues

#### Backend Issues
```bash
# ML model not loading
Error: "ml_model is None"
Solution: Ensure scikit-learn is installed and training data is available

# MongoDB connection failed  
Error: "ServerSelectionTimeoutError"
Solution: Verify MongoDB is running and connection string is correct

# CORS errors
Error: "Access-Control-Allow-Origin"
Solution: Update CORS_ORIGINS in environment variables
```

#### Frontend Issues
```bash
# API calls failing
Error: "Network Error" 
Solution: Verify REACT_APP_BACKEND_URL points to correct backend

# Build failures
Error: "Module not found"
Solution: Run yarn install to ensure all dependencies are installed

# Routing issues
Error: "Cannot GET /history"
Solution: Ensure React Router is properly configured
```

### Performance Optimization

#### Backend Optimization
```python
# Database query optimization
async def get_scan_history():
    # Use projection to limit returned fields
    history = await db.scan_history.find(
        {},
        {"content": 1, "risk_score": 1, "label": 1, "timestamp": 1}
    ).sort("timestamp", -1).limit(10).to_list(10)
    
    return history

# ML model caching
@lru_cache(maxsize=1000)
def classify_text(content: str):
    # Cache ML predictions for identical content
    return ml_model.predict_proba(vectorizer.transform([content]))
```

#### Frontend Optimization
```javascript
// Implement React.memo for expensive components
const ScanResult = React.memo(({ result }) => {
  // Component logic
});

// Use React.lazy for route-based code splitting
const HistoryPage = React.lazy(() => import('./pages/History'));
const StatsPage = React.lazy(() => import('./pages/Stats'));
```

## 📋 Deployment Checklist

### Pre-deployment
- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database migrations completed
- [ ] SSL certificates ready
- [ ] Domain configuration verified

### Deployment
- [ ] Code pushed to repository
- [ ] Deployment pipeline triggered
- [ ] Health checks passing
- [ ] Frontend/backend connectivity verified
- [ ] Database seeded with initial data

### Post-deployment
- [ ] Monitoring alerts configured
- [ ] Performance benchmarks established
- [ ] Backup procedures implemented
- [ ] Documentation updated
- [ ] Team access permissions set
