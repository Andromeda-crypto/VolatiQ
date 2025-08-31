# 🚀 VolatiQ Deployment Guide

## Step 1: Local Deployment ✅

### Quick Start (Current Status)
Your environment is validated and ready! The API should be running.

#### Start API Server
```bash
cd /Users/omanand/Desktop/Projects/VolatiQ
source venv/bin/activate
python api/app.py
```

#### Start Dashboard (New Terminal)
```bash
cd /Users/omanand/Desktop/Projects/VolatiQ
source venv/bin/activate
python dashboard/app.py
```

#### Test Your Local Deployment
```bash
# Test API
curl http://localhost:5000/health

# Test Prediction
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [[0.001, 0.02, 150.5, 149.8, 65.2]]}'

# Visit Dashboard
open http://localhost:8050
```

---

## Step 2: App Platform Deployment 🌐

### Option A: Heroku (Recommended for beginners)

#### 1. Prepare for Heroku
```bash
# Install Heroku CLI (if not installed)
brew install heroku/brew/heroku

# Login to Heroku
heroku login
```

#### 2. Create Heroku Apps
```bash
# Create API app
heroku create your-volatiq-api

# Create Dashboard app  
heroku create your-volatiq-dashboard
```

#### 3. Configure Environment Variables
```bash
# Set production environment for API
heroku config:set FLASK_ENV=production --app your-volatiq-api
heroku config:set SECRET_KEY=your-production-secret-key --app your-volatiq-api
heroku config:set API_HOST=0.0.0.0 --app your-volatiq-api
heroku config:set API_PORT=\$PORT --app your-volatiq-api

# Set dashboard environment  
heroku config:set API_URL=https://your-volatiq-api.herokuapp.com --app your-volatiq-dashboard
heroku config:set DASH_HOST=0.0.0.0 --app your-volatiq-dashboard
heroku config:set DASH_PORT=\$PORT --app your-volatiq-dashboard
```

#### 4. Create Procfiles
```bash
# API Procfile
echo "web: gunicorn -w 4 -b 0.0.0.0:\$PORT api.app:app" > Procfile

# Dashboard Procfile (for separate deployment)
echo "web: python dashboard/app.py" > Procfile.dashboard
```

#### 5. Deploy API
```bash
# Add git remote for API
heroku git:remote -a your-volatiq-api

# Deploy API
git add .
git commit -m "Deploy VolatiQ API"
git push heroku main
```

#### 6. Deploy Dashboard
```bash
# Create separate repo for dashboard or use same repo
heroku git:remote -a your-volatiq-dashboard -r dashboard

# Use dashboard Procfile
cp Procfile.dashboard Procfile
git add .
git commit -m "Deploy VolatiQ Dashboard"
git push dashboard main
```

### Option B: Railway (Modern alternative)

#### 1. Install Railway CLI
```bash
npm install -g @railway/cli
railway login
```

#### 2. Deploy API
```bash
# Initialize Railway project
railway init

# Set environment variables
railway variables set FLASK_ENV=production
railway variables set SECRET_KEY=your-production-secret-key
railway variables set API_HOST=0.0.0.0
railway variables set API_PORT=\$PORT

# Deploy
railway up
```

### Option C: Render (Free tier available)

#### 1. Connect GitHub Repository
1. Push your code to GitHub
2. Go to https://render.com
3. Connect your GitHub account
4. Select your VolatiQ repository

#### 2. Create Web Service for API
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn -w 4 -b 0.0.0.0:$PORT api.app:app`
- **Environment Variables**:
  ```
  FLASK_ENV=production
  SECRET_KEY=your-production-secret-key
  API_HOST=0.0.0.0
  API_PORT=$PORT
  ```

#### 3. Create Web Service for Dashboard
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python dashboard/app.py`
- **Environment Variables**:
  ```
  API_URL=https://your-api-service.onrender.com
  DASH_HOST=0.0.0.0
  DASH_PORT=$PORT
  ```

### Option D: Google Cloud Run

#### 1. Setup Google Cloud
```bash
# Install gcloud CLI
brew install google-cloud-sdk

# Login and set project
gcloud auth login
gcloud config set project your-project-id
```

#### 2. Deploy with Cloud Run
```bash
# Build and deploy API
gcloud run deploy volatiq-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# Deploy Dashboard (separate service)
gcloud run deploy volatiq-dashboard \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Step 3: Production Configuration 🔧

### Environment Variables for Production
Create a `.env` file for production:

```bash
# Production Environment
FLASK_ENV=production
SECRET_KEY=your-super-secure-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000
API_URL=https://your-api-domain.com

# Dashboard Configuration
DASH_HOST=0.0.0.0
DASH_PORT=8050

# Database (Optional)
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0

# External APIs
ALPHA_VANTAGE_API_KEY=your-api-key
YAHOO_FINANCE_API_KEY=your-api-key

# Monitoring
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO
```

### Database Setup (Optional)
For production with persistent storage:

```bash
# Add PostgreSQL addon (Heroku example)
heroku addons:create heroku-postgresql:mini --app your-volatiq-api

# Add Redis addon
heroku addons:create heroku-redis:mini --app your-volatiq-api
```

---

## Step 4: Testing Production Deployment 🧪

### Health Checks
```bash
# Test API health
curl https://your-api-domain.com/health

# Test prediction
curl -X POST https://your-api-domain.com/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [[0.001, 0.02, 150.5, 149.8, 65.2]]}'

# Visit dashboard
open https://your-dashboard-domain.com
```

### Performance Testing
```bash
# Run load tests
k6 run tests/performance/load-test.js
```

---

## Step 5: Monitoring & Maintenance 📊

### Set up Monitoring
1. **Sentry** for error tracking
2. **Datadog/New Relic** for APM
3. **Uptime monitoring** (Pingdom, UptimeRobot)

### Logs
```bash
# View Heroku logs
heroku logs --tail --app your-volatiq-api

# View Railway logs
railway logs

# View Render logs (in dashboard)
```

### Scaling
```bash
# Scale Heroku dynos
heroku ps:scale web=2 --app your-volatiq-api

# Railway auto-scales
# Render has auto-scaling options
```

---

## Quick Commands Reference 📝

### Local Development
```bash
# Start everything locally
source venv/bin/activate
python api/app.py &          # Terminal 1
python dashboard/app.py      # Terminal 2
```

### Heroku Deployment
```bash
# One-time setup
heroku create your-app-name
heroku config:set FLASK_ENV=production
echo "web: gunicorn -w 4 -b 0.0.0.0:\$PORT api.app:app" > Procfile

# Deploy
git add .
git commit -m "Deploy to production"
git push heroku main
```

### Check Status
```bash
# Local
curl http://localhost:5000/health

# Production
curl https://your-app.herokuapp.com/health
```

---

## 🎯 Recommended Next Steps

1. **Start Local**: Get both API and dashboard running locally
2. **Choose Platform**: Pick Heroku, Railway, or Render based on your needs
3. **Deploy API First**: Get the backend working in production
4. **Deploy Dashboard**: Connect dashboard to production API
5. **Test Everything**: Verify all endpoints and functionality
6. **Set up Monitoring**: Add error tracking and performance monitoring
7. **Custom Domain**: Point your own domain to the apps

**Your VolatiQ app will be live and ready to showcase on your resume!** 🌟
