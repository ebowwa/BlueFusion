#!/usr/bin/env python3
"""
Deployment and Configuration Guide wiki content
"""

CONTENT = """# BlueFusion Deployment Guide

## System Requirements

### Hardware Requirements
- **macOS**: 10.15 (Catalina) or later for native BLE support
- **USB Port**: Available USB port for sniffer dongle (optional)
- **Memory**: Minimum 4GB RAM, 8GB recommended
- **Storage**: 500MB for application and logs

### Software Requirements
- Python 3.9 or later
- pip package manager
- Virtual environment support (recommended)

## Installation Methods

### 1. Development Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/BlueFusion.git
cd BlueFusion

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install in development mode
pip install -e ".[dev,ai]"
```

### 2. Production Installation
```bash
# Install from PyPI (when available)
pip install bluefusion

# Or install from source
pip install git+https://github.com/yourusername/BlueFusion.git
```

### 3. Docker Installation
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000 7860

CMD ["python", "bluefusion.py", "start"]
```

```bash
# Build and run
docker build -t bluefusion .
docker run -p 8000:8000 -p 7860:7860 bluefusion
```

## Configuration

### Environment Variables
```bash
# API Configuration
export BLUEFUSION_API_HOST="0.0.0.0"
export BLUEFUSION_API_PORT="8000"
export BLUEFUSION_API_WORKERS="4"

# UI Configuration
export BLUEFUSION_UI_HOST="0.0.0.0"
export BLUEFUSION_UI_PORT="7860"
export BLUEFUSION_UI_SHARE="false"

# Logging
export BLUEFUSION_LOG_LEVEL="INFO"
export BLUEFUSION_LOG_FILE="/var/log/bluefusion/app.log"

# Security
export BLUEFUSION_API_KEY="your-secure-api-key"
export BLUEFUSION_ENABLE_AUTH="true"
```

### Configuration File
Create `config.yaml` in the project root:

```yaml
# config.yaml
api:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  cors_origins:
    - "http://localhost:7860"
    - "https://yourdomain.com"

ui:
  host: "0.0.0.0"
  port: 7860
  share: false
  theme: "default"

interfaces:
  macbook:
    enabled: true
    scan_timeout: 30
    max_connections: 5
  
  sniffer:
    enabled: false
    port: "/dev/tty.usbserial-*"
    baudrate: 115200
    channels: [37, 38, 39]

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "/var/log/bluefusion/app.log"
  max_size: "10MB"
  backup_count: 5

security:
  enable_auth: false
  api_key: ""
  allowed_ips: []
  rate_limit:
    enabled: true
    requests_per_minute: 100

database:
  enabled: false
  url: "sqlite:///bluefusion.db"
  
cache:
  enabled: true
  ttl: 300  # seconds
  max_size: 1000
```

## Deployment Scenarios

### 1. Local Development
```bash
# Start with default settings
python bluefusion.py start

# Start with custom configuration
python bluefusion.py start --config config.yaml
```

### 2. Production Server

#### Using systemd (Linux/macOS)
```ini
# /etc/systemd/system/bluefusion.service
[Unit]
Description=BlueFusion BLE Monitoring System
After=network.target

[Service]
Type=simple
User=bluefusion
WorkingDirectory=/opt/bluefusion
Environment="PATH=/opt/bluefusion/venv/bin"
ExecStart=/opt/bluefusion/venv/bin/python /opt/bluefusion/bluefusion.py start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable bluefusion
sudo systemctl start bluefusion
sudo systemctl status bluefusion
```

#### Using PM2 (Node.js Process Manager)
```bash
# Install PM2
npm install -g pm2

# Start BlueFusion
pm2 start bluefusion.py --interpreter python3 --name bluefusion -- start

# Save PM2 configuration
pm2 save
pm2 startup
```

### 3. Cloud Deployment

#### AWS EC2
```bash
# User data script for EC2 instance
#!/bin/bash
yum update -y
yum install -y python3 python3-pip git

# Clone and install BlueFusion
cd /opt
git clone https://github.com/yourusername/BlueFusion.git
cd BlueFusion
pip3 install -e .

# Start service
python3 bluefusion.py start --api-host 0.0.0.0
```

#### Heroku
```yaml
# Procfile
web: python bluefusion.py api --port $PORT
worker: python bluefusion.py ui --port $PORT
```

```yaml
# runtime.txt
python-3.9.16
```

### 4. Kubernetes Deployment
```yaml
# bluefusion-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bluefusion
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bluefusion
  template:
    metadata:
      labels:
        app: bluefusion
    spec:
      containers:
      - name: bluefusion
        image: bluefusion:latest
        ports:
        - containerPort: 8000
          name: api
        - containerPort: 7860
          name: ui
        env:
        - name: BLUEFUSION_API_HOST
          value: "0.0.0.0"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: bluefusion-service
spec:
  selector:
    app: bluefusion
  ports:
  - name: api
    port: 8000
    targetPort: 8000
  - name: ui
    port: 7860
    targetPort: 7860
  type: LoadBalancer
```

## Performance Tuning

### API Server
```python
# Increase worker processes for better concurrency
python bluefusion.py api --workers 8

# Enable async mode
python bluefusion.py api --async-mode

# Configure connection pooling
python bluefusion.py api --pool-size 100
```

### Memory Optimization
```bash
# Limit packet buffer size
export BLUEFUSION_MAX_PACKET_BUFFER=10000

# Enable packet compression
export BLUEFUSION_COMPRESS_PACKETS=true

# Set cache limits
export BLUEFUSION_CACHE_MAX_SIZE=1000
```

## Monitoring

### Health Checks
```bash
# API health check
curl http://localhost:8000/health

# UI health check
curl http://localhost:7860/health
```

### Metrics Collection
```python
# Enable Prometheus metrics
python bluefusion.py start --enable-metrics

# Access metrics endpoint
curl http://localhost:8000/metrics
```

### Logging Configuration
```python
# Set log level
python bluefusion.py start --log-level DEBUG

# Enable structured logging
python bluefusion.py start --log-format json

# Log to file
python bluefusion.py start --log-file /var/log/bluefusion.log
```

## Backup and Recovery

### Data Backup
```bash
# Backup captured data
python bluefusion.py backup --output backup.tar.gz

# Restore from backup
python bluefusion.py restore --input backup.tar.gz
```

### Configuration Backup
```bash
# Export configuration
python bluefusion.py config export > config-backup.yaml

# Import configuration
python bluefusion.py config import < config-backup.yaml
```

## Security Hardening

### Network Security
```nginx
# Nginx reverse proxy configuration
server {
    listen 443 ssl;
    server_name bluefusion.yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/bluefusion.crt;
    ssl_certificate_key /etc/ssl/private/bluefusion.key;
    
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
        proxy_pass http://localhost:7860/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Access Control
```bash
# Enable API authentication
export BLUEFUSION_ENABLE_AUTH=true
export BLUEFUSION_API_KEY=$(openssl rand -hex 32)

# Restrict IP addresses
export BLUEFUSION_ALLOWED_IPS="192.168.1.0/24,10.0.0.0/8"
```

## Troubleshooting Deployment

### Common Issues

1. **Port Already in Use**
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

2. **Permission Errors**
```bash
# Fix permissions
sudo chown -R $USER:$USER /opt/bluefusion
chmod +x bluefusion.py
```

3. **Module Import Errors**
```bash
# Reinstall dependencies
pip install --upgrade --force-reinstall -e .
```

4. **BLE Access Denied (macOS)**
```bash
# Grant Bluetooth permissions
# System Preferences > Security & Privacy > Privacy > Bluetooth
# Add Terminal or your IDE
```
"""