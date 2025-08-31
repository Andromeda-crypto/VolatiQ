# VolatiQ Deployment Guide

## Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB RAM available
- Python 3.11 (for local development)

### Production Deployment

1. **Clone and Setup**
```bash
git clone <repository-url>
cd VolatiQ
cp env.example .env
# Edit .env file with your production values
```

2. **Build and Deploy**
```bash
# Build the application
docker-compose build

# Start all services
docker-compose up -d

# Check health
curl http://localhost:5000/health
curl http://localhost:8050  # Dashboard
```

3. **Access Applications**
- API: http://localhost:5000
- Dashboard: http://localhost:8050
- Database: localhost:5432 (if enabled)

### Local Development

1. **Setup Virtual Environment**
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Train Model (if needed)**
```bash
python model/train.py
```

3. **Run Services**
```bash
# Terminal 1 - API
python api/app.py

# Terminal 2 - Dashboard  
python dashboard/app.py
```

## Cloud Deployment Options

### AWS Deployment

**Option 1: ECS with Fargate**
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker build -t volatiq .
docker tag volatiq:latest <account>.dkr.ecr.us-east-1.amazonaws.com/volatiq:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/volatiq:latest

# Deploy with CloudFormation or Terraform
```

**Option 2: EC2 with Docker Compose**
```bash
# On EC2 instance
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install docker-compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Deploy application
git clone <repository-url>
cd VolatiQ
docker-compose up -d
```

### Google Cloud Platform

**Cloud Run Deployment**
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/volatiq
gcloud run deploy --image gcr.io/PROJECT-ID/volatiq --platform managed
```

### Azure Deployment

**Container Instances**
```bash
# Build and push to ACR
az acr build --registry <registry-name> --image volatiq .
az container create --resource-group myResourceGroup --name volatiq --image <registry-name>.azurecr.io/volatiq:latest
```

## Environment Configuration

### Required Environment Variables

```bash
# Application
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
API_HOST=0.0.0.0
API_PORT=5000

# Database (optional)
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0

# Security
JWT_SECRET_KEY=your-jwt-secret

# External APIs
ALPHA_VANTAGE_API_KEY=your-api-key
```

### Database Setup

**PostgreSQL (Optional)**
```sql
-- Create database
CREATE DATABASE volatiq;
CREATE USER volatiq WITH ENCRYPTED PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE volatiq TO volatiq;

-- Tables will be created automatically on first run
```

## Monitoring & Observability

### Health Checks
- API Health: `GET /health`
- Model Status: `GET /metrics`
- Dashboard: HTTP 200 on root path

### Logging
- API logs: `logs/api.log`
- Application logs: Docker container logs
- Log levels: DEBUG, INFO, WARNING, ERROR

### Metrics Collection
```python
# Custom metrics endpoint
GET /metrics
{
  "model_info": {...},
  "system_info": {...},
  "performance_metrics": {...}
}
```

## Security Considerations

1. **API Security**
   - Rate limiting: 200/day, 50/hour per IP
   - Input validation on all endpoints
   - Error handling without data leakage

2. **Infrastructure Security**
   - Use HTTPS in production
   - Secure environment variables
   - Network isolation with Docker
   - Regular security updates

3. **Model Security**
   - Model file integrity checks
   - Secure model storage
   - Audit trail for predictions

## Performance Optimization

### API Performance
- Prediction batch limits
- Async processing for large batches
- Model caching
- Response compression

### Database Performance
- Connection pooling
- Query optimization
- Indexing strategy
- Read replicas for scaling

### Infrastructure Scaling
```yaml
# docker-compose scaling
docker-compose up --scale volatiq-api=3

# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: volatiq-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: volatiq-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Troubleshooting

### Common Issues

1. **Model Loading Errors**
```bash
# Check model files exist
ls -la model/saved_model/
# Check permissions
docker exec volatiq-api ls -la /app/model/saved_model/
```

2. **Memory Issues**
```bash
# Check memory usage
docker stats
# Increase container memory limits
```

3. **Database Connection Issues**
```bash
# Test database connectivity
docker exec volatiq-api pg_isready -h volatiq-db -p 5432
```

### Debug Mode
```bash
# Run with debug logging
FLASK_ENV=development LOG_LEVEL=DEBUG docker-compose up
```

## Maintenance

### Model Updates
1. Train new model
2. Save to `model/saved_model/`
3. Restart API service
4. Validate with health check

### Data Updates
1. Update `data/market_data.csv`
2. Retrain model if needed
3. Deploy updated model

### Backup Strategy
- Database: Daily backups
- Model files: Version control
- Configuration: Environment variables backup

## Support

For deployment issues:
1. Check logs: `docker-compose logs`
2. Verify health endpoints
3. Review environment configuration
4. Consult troubleshooting section
