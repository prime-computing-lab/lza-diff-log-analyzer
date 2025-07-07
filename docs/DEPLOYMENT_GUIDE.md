# LZA Diff Analyzer - Deployment Guide

## Overview

This guide provides comprehensive deployment instructions for the LZA Diff Analyzer across different environments and use cases. It covers everything from local development setup to enterprise production deployment, focusing on the needs of cloud administrators and DevOps engineers.

## Table of Contents

1. [Quick Start Deployment](#quick-start-deployment)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Container Deployment](#container-deployment)
5. [CI/CD Integration](#cicd-integration)
6. [Configuration Management](#configuration-management)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start Deployment

### Prerequisites
- Python 3.10 or higher
- Git (for source code access)
- 2GB+ available RAM
- 500MB+ disk space

### Rapid Installation (UV - Recommended)

```bash
# Install UV package manager (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal

# Clone the repository
git clone <repository-url>
cd lza-diff-analyzer

# Install with all features
uv sync --extra llm --extra dev

# Activate the virtual environment
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate    # Windows

# Verify installation
lza-analyze --version
```

### Alternative Installation (pip)

```bash
# Clone the repository
git clone <repository-url>
cd lza-diff-analyzer

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -e ".[llm,dev]"

# Verify installation
lza-analyze --version
```

### First Analysis

```bash
# Basic analysis (LLM enabled by default)
lza-analyze --input-dir /path/to/diff-logs

# Rule-based analysis only (disable LLM)
lza-analyze --input-dir /path/to/diff-logs --disable-llm

# With specific LLM provider
lza-analyze --input-dir /path/to/diff-logs --llm-provider openai

# Generate comprehensive reports
lza-analyze --input-dir /path/to/diff-logs --generate-reports
```

---

## Local Development Setup

### Development Environment

#### Full Development Setup
```bash
# Clone with development tools
git clone <repository-url>
cd lza-diff-analyzer

# Install with all development dependencies
uv sync --extra llm --extra dev

# Install pre-commit hooks (optional)
pre-commit install

# Run tests to verify setup
uv run pytest

# Run linting
uv run black src/
uv run isort src/
uv run flake8 src/
uv run mypy src/
```

#### IDE Configuration

**VS Code Setup**:
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.provider": "isort"
}
```

**PyCharm Setup**:
- Configure Python interpreter to `.venv/bin/python`
- Enable Black formatter in settings
- Configure pytest as test runner
- Set up type checking with mypy

### LLM Provider Setup

#### Ollama (Local Models)
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Download recommended models
ollama pull qwen2.5:7b          # Fast, good quality
ollama pull qwen3:30b-a3b      # High-quality model (current default)
ollama pull deepseek-r1:latest  # Advanced reasoning
ollama pull llama3.2:3b        # Lightweight option

# Verify model availability
ollama list
```

#### Cloud Providers
```bash
# OpenAI setup
export OPENAI_API_KEY="your-openai-api-key"

# Anthropic setup
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Verify configuration
lza-analyze analyze --input-dir sample-data --llm-provider openai
```

### Configuration Files

#### LLM Configuration (`config/llm_config.yaml`)
```yaml
# Development configuration
default_provider: ollama
max_retries: 3
retry_delay: 1.0

fallback_chain:
  - ollama
  - openai      # Requires API key
  - anthropic   # Requires API key

providers:
  ollama:
    provider: ollama
    model: "qwen3:30b-a3b"
    temperature: 0.1
    max_tokens: 4096
    timeout: 30
    base_url: "http://localhost:11434"
    enabled: true
    
  openai:
    provider: openai
    model: "gpt-4o-mini"
    temperature: 0.1
    max_tokens: 4096
    timeout: 30
    api_key: ${OPENAI_API_KEY}
    enabled: false  # Enable when API key is set
```

---

## Production Deployment

### Infrastructure Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **Memory**: 4GB RAM
- **Storage**: 10GB available space
- **Network**: Internet access for cloud LLM providers
- **OS**: Linux (Ubuntu 20.04+), macOS 10.15+, Windows 10+

#### Recommended Production Specs
- **CPU**: 4+ cores
- **Memory**: 8GB+ RAM
- **Storage**: 50GB+ SSD
- **Network**: Stable internet connection (100Mbps+)
- **OS**: Linux server distribution (Ubuntu 22.04 LTS recommended)

### Production Installation

#### System Preparation
```bash
# Update system packages (Ubuntu/Debian)
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+
sudo apt install python3.10 python3.10-venv python3.10-dev -y

# Install system dependencies
sudo apt install git curl build-essential -y

# Create dedicated user (recommended)
sudo useradd -m -s /bin/bash lza-analyzer
sudo su - lza-analyzer
```

#### Application Installation
```bash
# Create application directory
mkdir -p /opt/lza-diff-analyzer
cd /opt/lza-diff-analyzer

# Clone repository
git clone <repository-url> .

# Install UV for production
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Install application
uv sync --extra llm

# Create configuration
mkdir -p config
cp config/llm_config.yaml.example config/llm_config.yaml
# Edit configuration as needed
```

#### Service Configuration

**Systemd Service** (`/etc/systemd/system/lza-analyzer.service`):
```ini
[Unit]
Description=LZA Diff Analyzer Service
After=network.target

[Service]
Type=simple
User=lza-analyzer
Group=lza-analyzer
WorkingDirectory=/opt/lza-diff-analyzer
Environment=PATH=/opt/lza-diff-analyzer/.venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/opt/lza-diff-analyzer/.venv/bin/lza-analyze analyze --input-dir /data/diff-logs --output-dir /data/output
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/data

[Install]
WantedBy=multi-user.target
```

#### Directory Structure
```
/opt/lza-diff-analyzer/          # Application root
├── .venv/                       # Virtual environment
├── src/                         # Source code
├── config/                      # Configuration files
├── docs/                        # Documentation
└── logs/                        # Application logs

/data/                           # Data directory
├── diff-logs/                   # Input diff files
├── output/                      # Analysis results
└── reports/                     # Generated reports
```

### Environment Variables

#### Production Environment File (`.env`)
```bash
# LLM Provider Configuration
OPENAI_API_KEY=your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here

# Application Configuration
LZA_OUTPUT_DIR=/data/output
LZA_LOG_LEVEL=INFO
LZA_MAX_WORKERS=4

# Security Configuration
LZA_SECURE_MODE=true
LZA_API_RATE_LIMIT=100

# Monitoring
LZA_METRICS_ENABLED=true
LZA_HEALTH_CHECK_PORT=8080
```

#### Loading Environment
```bash
# In startup scripts
set -a  # Export all variables
source /opt/lza-diff-analyzer/.env
set +a  # Stop exporting

# Or use systemd EnvironmentFile
# EnvironmentFile=/opt/lza-diff-analyzer/.env
```

---

## Container Deployment

### Docker Configuration

#### Dockerfile
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Create app directory
WORKDIR /app

# Copy application files
COPY . .

# Install dependencies
RUN uv sync --extra llm

# Create non-root user
RUN useradd -m -u 1000 lza-user && \
    chown -R lza-user:lza-user /app
USER lza-user

# Expose health check port
EXPOSE 8080

# Default command
CMD [".venv/bin/lza-analyze", "analyze", "--input-dir", "/data/input", "--output-dir", "/data/output"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  lza-analyzer:
    build: .
    container_name: lza-diff-analyzer
    volumes:
      - ./data/input:/data/input:ro
      - ./data/output:/data/output
      - ./config:/app/config:ro
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    restart: unless-stopped
    
  # Optional: Ollama for local LLM
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

volumes:
  ollama_data:
```

#### Container Management
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f lza-analyzer

# Execute analysis
docker-compose exec lza-analyzer lza-analyze analyze --input-dir /data/input

# Stop services
docker-compose down
```

### Kubernetes Deployment

#### ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: lza-config
data:
  llm_config.yaml: |
    default_provider: ollama
    fallback_chain: [ollama, openai]
    providers:
      ollama:
        provider: ollama
        model: "qwen3:30b-a3b"
        base_url: "http://ollama-service:11434"
        enabled: true
```

#### Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lza-analyzer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: lza-analyzer
  template:
    metadata:
      labels:
        app: lza-analyzer
    spec:
      containers:
      - name: lza-analyzer
        image: lza-diff-analyzer:latest
        ports:
        - containerPort: 8080
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: lza-secrets
              key: openai-api-key
        volumeMounts:
        - name: config
          mountPath: /app/config
        - name: data
          mountPath: /data
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2"
      volumes:
      - name: config
        configMap:
          name: lza-config
      - name: data
        persistentVolumeClaim:
          claimName: lza-data-pvc
```

---

## CI/CD Integration

### GitHub Actions

#### Workflow Configuration (`.github/workflows/deploy.yml`)
```yaml
name: Deploy LZA Analyzer

on:
  push:
    branches: [main]
  release:
    types: [published]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install UV
      run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
    - name: Install dependencies
      run: uv sync --extra dev
      
    - name: Run tests
      run: |
        uv run pytest
        uv run mypy src/
        uv run flake8 src/
        
    - name: Security audit
      run: uv run pip-audit

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t lza-analyzer:${{ github.sha }} .
      
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push lza-analyzer:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Deploy to production
      run: |
        # Deployment commands here
        echo "Deploying to production..."
```

### Jenkins Pipeline

#### Jenkinsfile
```groovy
pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.11'
        DOCKER_REGISTRY = 'your-registry.com'
    }
    
    stages {
        stage('Test') {
            steps {
                sh '''
                    python -m venv venv
                    . venv/bin/activate
                    pip install uv
                    uv sync --extra dev
                    uv run pytest
                '''
            }
        }
        
        stage('Security Scan') {
            steps {
                sh 'uv run pip-audit'
                sh 'docker run --rm -v $PWD:/app securecodewarrior/docker-scan /app'
            }
        }
        
        stage('Build') {
            steps {
                sh 'docker build -t ${DOCKER_REGISTRY}/lza-analyzer:${BUILD_NUMBER} .'
            }
        }
        
        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    docker push ${DOCKER_REGISTRY}/lza-analyzer:${BUILD_NUMBER}
                    kubectl set image deployment/lza-analyzer lza-analyzer=${DOCKER_REGISTRY}/lza-analyzer:${BUILD_NUMBER}
                '''
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
    }
}
```

---

## Configuration Management

### Environment-Specific Configuration

#### Development
```yaml
# config/llm_config.dev.yaml
default_provider: ollama
max_retries: 1
retry_delay: 0.5

providers:
  ollama:
    model: "qwen3:30b-a3b"
    timeout: 10
    enabled: true
```

#### Staging
```yaml
# config/llm_config.staging.yaml
default_provider: openai
max_retries: 2
retry_delay: 1.0

fallback_chain:
  - openai
  - ollama

providers:
  openai:
    model: "gpt-4o-mini"
    timeout: 15
    enabled: true
```

#### Production
```yaml
# config/llm_config.prod.yaml
default_provider: anthropic
max_retries: 3
retry_delay: 2.0

fallback_chain:
  - anthropic
  - openai
  - ollama

providers:
  anthropic:
    model: "claude-3-haiku-20240307"
    timeout: 30
    enabled: true
```

### Configuration Validation

```bash
# Validate configuration before deployment
python -c "
from src.llm.config import LLMConfigManager
try:
    config = LLMConfigManager.from_yaml_file('config/llm_config.yaml')
    print('Configuration valid')
except Exception as e:
    print(f'Configuration error: {e}')
    exit(1)
"
```

---

## Monitoring and Maintenance

### Health Checks

#### Application Health
```python
# health_check.py
import requests
import sys

def check_health():
    try:
        # Check application availability
        response = requests.get('http://localhost:8080/health', timeout=5)
        if response.status_code == 200:
            return True
    except:
        pass
    return False

if __name__ == '__main__':
    if check_health():
        print('OK')
        sys.exit(0)
    else:
        print('FAIL')
        sys.exit(1)
```

#### LLM Provider Health
```bash
#!/bin/bash
# check_llm_providers.sh

# Check Ollama
curl -f http://localhost:11434/api/tags >/dev/null 2>&1
OLLAMA_STATUS=$?

# Check OpenAI (if API key is set)
if [ -n "$OPENAI_API_KEY" ]; then
    curl -f -H "Authorization: Bearer $OPENAI_API_KEY" \
         https://api.openai.com/v1/models >/dev/null 2>&1
    OPENAI_STATUS=$?
fi

echo "Ollama: $([ $OLLAMA_STATUS -eq 0 ] && echo 'OK' || echo 'FAIL')"
echo "OpenAI: $([ $OPENAI_STATUS -eq 0 ] && echo 'OK' || echo 'FAIL')"
```

### Logging Configuration

#### Python Logging
```python
# logging_config.py
import logging
import logging.handlers

def configure_logging(level='INFO', log_file='/var/log/lza-analyzer.log'):
    logger = logging.getLogger('lza-analyzer')
    logger.setLevel(getattr(logging, level))
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter('%(levelname)s: %(message)s')
    )
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
```

### Performance Monitoring

#### Metrics Collection
```python
# metrics.py
import time
import psutil
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        result = func(*args, **kwargs)
        
        duration = time.time() - start_time
        memory_used = psutil.Process().memory_info().rss - start_memory
        
        print(f"Function {func.__name__}:")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Memory: {memory_used / 1024 / 1024:.2f}MB")
        
        return result
    return wrapper
```

### Backup and Recovery

#### Data Backup
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/lza-analyzer/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup configuration
cp -r /opt/lza-diff-analyzer/config "$BACKUP_DIR/"

# Backup data
tar -czf "$BACKUP_DIR/data.tar.gz" /data/

# Backup logs
cp -r /var/log/lza-analyzer.log* "$BACKUP_DIR/"

echo "Backup completed: $BACKUP_DIR"
```

---

## Troubleshooting

### Common Issues

#### Installation Problems

**UV Installation Fails**:
```bash
# Alternative installation methods
pip install uv
# or
conda install -c conda-forge uv
```

**Python Version Issues**:
```bash
# Check Python version
python --version
# Install specific version (Ubuntu)
sudo apt install python3.11-dev python3.11-venv
```

#### Runtime Issues

**LLM Connection Failures**:
```bash
# Check Ollama service
systemctl status ollama
curl http://localhost:11434/api/tags

# Check API keys
echo $OPENAI_API_KEY | wc -c  # Should be > 50 characters
```

**Memory Issues**:
```bash
# Monitor memory usage
htop
# Increase virtual memory
sudo sysctl vm.swappiness=10
```

#### Configuration Issues

**YAML Parsing Errors**:
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/llm_config.yaml'))"

# Check indentation
cat -A config/llm_config.yaml
```

### Debug Mode

#### Enable Verbose Logging
```bash
# Set debug environment
export LZA_LOG_LEVEL=DEBUG

# Run with verbose output
lza-analyze analyze --input-dir /path/to/diff-logs --verbose
```

#### Debug Configuration
```python
# Debug startup issues
python -c "
import sys
sys.path.insert(0, 'src')
from cli.simple_main import main
main(['--help'])
"
```

### Support Resources

#### Log Analysis
```bash
# View recent errors
grep -i error /var/log/lza-analyzer.log | tail -20

# Monitor real-time logs
tail -f /var/log/lza-analyzer.log

# Search for specific issues
grep -i "llm\|connection\|timeout" /var/log/lza-analyzer.log
```

#### System Information
```bash
# System resources
free -h
df -h
cat /proc/cpuinfo | grep processor | wc -l

# Python environment
python --version
pip list | grep -E "(pydantic|click|rich)"

# Network connectivity
curl -I https://api.openai.com
curl -I https://api.anthropic.com
```

This deployment guide provides comprehensive coverage for deploying the LZA Diff Analyzer in various environments, from local development to enterprise production systems. The modular approach allows teams to implement the appropriate level of complexity for their specific needs while maintaining security and reliability standards.