# Production Deployment Guide

## Overview
This guide covers deploying the Advanced AI Document Extraction System to production environments.

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **RAM**: Minimum 4GB, recommended 8GB
- **Storage**: 10GB free space for models and cache
- **OS**: Windows, Linux, or macOS

### API Keys Required
1. **OpenAI API Key** (for GPT-4 Vision)
2. **Anthropic API Key** (for Claude models)

## Installation

### 1. Environment Setup

```powershell
# Clone repository
git clone <repository-url>
cd "Advanced Ai Project"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Custom configuration
MAX_WORKERS=4
CACHE_TTL_HOURS=168
METRICS_ENABLED=true
```

**Security Note**: Never commit `.env` files to version control!

### 3. Verify Installation

```powershell
# Check environment variables
python check_env_vars.py

# Run test suite
python tests/run_all_tests.py
```

## Configuration

### Performance Tuning

Edit configuration in your code or environment:

```python
# Parallel processing workers
MAX_WORKERS = 4  # Adjust based on CPU cores

# LLM cache settings
CACHE_TTL_HOURS = 168  # 7 days

# API rate limiting
API_REQUESTS_PER_MINUTE = 60
```

### Memory Optimization

For limited memory environments:

```python
# Reduce batch sizes
CHART_BATCH_SIZE = 5  # Instead of 10

# Enable aggressive caching
ENABLE_LLM_CACHE = True
CACHE_DIR = ".cache/llm"
```

## Deployment Options

### Option 1: Local Server

```powershell
# Start web interface
python app.py
```

Access at: `http://localhost:5000`

### Option 2: Docker Container

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "app.py"]
```

Build and run:

```powershell
# Build image
docker build -t ai-document-extractor .

# Run container
docker run -p 5000:5000 -e OPENAI_API_KEY=$env:OPENAI_API_KEY ai-document-extractor
```

### Option 3: Cloud Deployment (Azure)

#### Azure App Service

```powershell
# Login to Azure
az login

# Create resource group
az group create --name ai-extractor-rg --location eastus

# Create App Service plan
az appservice plan create --name ai-extractor-plan --resource-group ai-extractor-rg --sku B1

# Create web app
az webapp create --name ai-document-extractor --resource-group ai-extractor-rg --plan ai-extractor-plan --runtime "PYTHON:3.10"

# Configure environment variables
az webapp config appsettings set --name ai-document-extractor --resource-group ai-extractor-rg --settings OPENAI_API_KEY=$env:OPENAI_API_KEY

# Deploy code
az webapp up --name ai-document-extractor --resource-group ai-extractor-rg
```

## Monitoring Setup

### 1. Enable Metrics Collection

```python
from src.utils.metrics import get_metrics_collector, AlertSystem

# Initialize metrics
metrics = get_metrics_collector(metrics_dir="metrics")

# Setup alerts
alerts = AlertSystem(metrics)
alerts.thresholds["validation_failure_rate"] = 0.2  # 20%
alerts.thresholds["api_cost_per_hour"] = 10.0  # $10/hour
```

### 2. Export Metrics Regularly

```python
# Export metrics daily
import schedule

def export_daily_metrics():
    metrics = get_metrics_collector()
    metrics.export_metrics()
    
    # Check alerts
    alert_system = AlertSystem(metrics)
    alerts = alert_system.check_alerts()
    
    if alerts:
        # Send notification (email, Slack, etc.)
        send_alert_notification(alerts)

schedule.every().day.at("00:00").do(export_daily_metrics)
```

### 3. Setup Log Aggregation

Configure logging to file:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/application.log'),
        logging.StreamHandler()
    ]
)
```

## Performance Optimization

### 1. Enable LLM Caching

```python
from src.utils.llm_cache import get_llm_cache

cache = get_llm_cache(cache_dir=".cache/llm", ttl_hours=168)
```

### 2. Parallel Chart Processing

```python
from src.utils.parallel_processor import ChartBatchProcessor

processor = ChartBatchProcessor(
    chart_analyzer=your_chart_analyzer,
    max_workers=3  # Adjust based on API rate limits
)

results = processor.analyze_charts(chart_paths)
```

### 3. Reference Data Preloading

```python
from src.utils.reference_data_manager import ReferenceDataManager

ref_manager = ReferenceDataManager(base_dir="reference_data")

# Preload reference documents on startup
for fund_name in all_funds:
    ref_manager.load_reference_data_for_fund(fund_name)
```

## Backup and Recovery

### Database Backups

```powershell
# Backup outputs directory
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Compress-Archive -Path outputs -DestinationPath "backups/outputs_$timestamp.zip"

# Backup reference data
Compress-Archive -Path reference_data -DestinationPath "backups/reference_data_$timestamp.zip"
```

### Automated Backup Script

```powershell
# backup.ps1
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "backups/$timestamp"

New-Item -ItemType Directory -Path $backupDir -Force

# Backup critical directories
Copy-Item -Recurse outputs $backupDir/
Copy-Item -Recurse reference_data $backupDir/
Copy-Item -Recurse metrics $backupDir/

# Compress
Compress-Archive -Path $backupDir -DestinationPath "backups/backup_$timestamp.zip"
Remove-Item -Recurse $backupDir

Write-Host "Backup completed: backup_$timestamp.zip"
```

Schedule with Task Scheduler (Windows) or cron (Linux).

## Security Best Practices

### 1. API Key Management

```powershell
# Use Azure Key Vault
az keyvault create --name ai-extractor-vault --resource-group ai-extractor-rg
az keyvault secret set --vault-name ai-extractor-vault --name openai-api-key --value $env:OPENAI_API_KEY

# Retrieve in application
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://ai-extractor-vault.vault.azure.net/", credential=credential)
api_key = client.get_secret("openai-api-key").value
```

### 2. Input Validation

```python
# Validate uploaded files
ALLOWED_EXTENSIONS = {'.pdf', '.pptx', '.docx'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def validate_upload(file):
    if file.size > MAX_FILE_SIZE:
        raise ValueError("File too large")
    
    if not any(file.filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise ValueError("Invalid file type")
```

### 3. Rate Limiting

```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["100 per hour"]
)

@app.route("/extract", methods=["POST"])
@limiter.limit("10 per minute")
def extract_document():
    # Processing logic
    pass
```

## Troubleshooting

### Common Issues

#### 1. Out of Memory Errors

**Solution**: Reduce batch sizes and enable streaming:

```python
CHART_BATCH_SIZE = 3  # Reduce from default
ENABLE_STREAMING = True
```

#### 2. API Rate Limit Exceeded

**Solution**: Implement exponential backoff:

```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except RateLimitError:
                    wait = 2 ** attempt
                    time.sleep(wait)
            raise
        return wrapper
    return decorator
```

#### 3. Slow Performance

**Solution**: Enable all optimizations:

```python
# Enable caching
ENABLE_LLM_CACHE = True

# Use parallel processing
ENABLE_PARALLEL_CHARTS = True
MAX_WORKERS = 4

# Preload reference data
PRELOAD_REFERENCE_DATA = True
```

### Log Analysis

```powershell
# Search for errors
Select-String -Path logs/application.log -Pattern "ERROR"

# Check validation failures
Select-String -Path logs/application.log -Pattern "Validation failed"

# Monitor API usage
Select-String -Path logs/application.log -Pattern "API call"
```

## Health Checks

### Application Health Endpoint

```python
@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    
    # Check API connectivity
    api_status = check_api_connection()
    
    # Check disk space
    disk_space = check_disk_space()
    
    # Check memory
    memory_usage = check_memory_usage()
    
    return jsonify({
        "status": "healthy" if all([api_status, disk_space, memory_usage]) else "unhealthy",
        "api_connection": api_status,
        "disk_space_gb": disk_space,
        "memory_usage_percent": memory_usage,
        "timestamp": datetime.utcnow().isoformat()
    })
```

### Monitoring Script

```python
# monitor.py
import requests
import time

def monitor_health():
    """Monitor application health"""
    while True:
        try:
            response = requests.get("http://localhost:5000/health", timeout=10)
            health = response.json()
            
            if health["status"] != "healthy":
                send_alert(f"Health check failed: {health}")
            
        except Exception as e:
            send_alert(f"Health check error: {e}")
        
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    monitor_health()
```

## Scaling Considerations

### Horizontal Scaling

For high-volume processing:

1. **Load Balancer**: Use Nginx or Azure Load Balancer
2. **Multiple Instances**: Run multiple app instances
3. **Shared Storage**: Use Azure Blob Storage for outputs
4. **Redis Cache**: Share LLM cache across instances

```python
# Use Redis for distributed caching
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_response(prompt):
    cached = redis_client.get(prompt)
    if cached:
        return json.loads(cached)
    return None

def cache_response(prompt, response):
    redis_client.setex(prompt, 7*24*3600, json.dumps(response))
```

### Vertical Scaling

- **CPU**: 4+ cores recommended for parallel processing
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: SSD for faster I/O

## Cost Optimization

### Track API Costs

```python
from src.utils.metrics import get_metrics_collector

metrics = get_metrics_collector()

# Log costs
metrics.log_api_usage(
    api_name="openai",
    model="gpt-4-vision",
    operation="chart_analysis",
    tokens_used=1500,
    duration_seconds=2.5,
    cost_estimate=0.045
)

# Generate cost report
summary = metrics.get_summary(hours=24)
print(f"Daily API cost: ${summary['api_usage']['total_cost']:.2f}")
```

### Cost Reduction Strategies

1. **Enable caching** (can reduce costs by 50-70%)
2. **Use cheaper models** for simple tasks
3. **Batch processing** for efficiency
4. **Monitor and alert** on high costs

## Support and Maintenance

### Update Schedule

- **Security updates**: Immediately
- **Dependency updates**: Monthly
- **Feature updates**: Quarterly

### Maintenance Tasks

```powershell
# Weekly maintenance
python -c "from src.utils.llm_cache import get_llm_cache; get_llm_cache().clear_expired()"
python -c "from src.utils.metrics import get_metrics_collector; get_metrics_collector().export_metrics()"

# Monthly maintenance
pip list --outdated
python tests/run_all_tests.py
```

## Contact Information

For production support:
- **Documentation**: See `docs/` directory
- **Issues**: GitHub Issues
- **Security**: Report to security@example.com

---

**Last Updated**: 2024
**Version**: 1.0
