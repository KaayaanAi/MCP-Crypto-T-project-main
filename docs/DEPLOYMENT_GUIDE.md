# MCP Crypto Trading Analysis - Production Deployment Guide

## 🚀 Overview

This comprehensive guide covers the complete production deployment of the MCP Crypto Trading Analysis platform for Kaayaan infrastructure integration. The system provides 7 intelligent trading tools with enterprise-grade features including real-time monitoring, automated alerting, comprehensive risk management, and seamless n8n workflow integration.

### Key Features
- **Professional Trading Tools**: 7 specialized MCP tools for institutional-grade analysis
- **Kaayaan Infrastructure**: Native integration with MongoDB, Redis, PostgreSQL, and WhatsApp
- **Production Ready**: Docker containerization with health monitoring and auto-scaling
- **n8n Compatible**: Direct MCP Client node integration for workflow automation
- **Real-time Analytics**: Sub-second market analysis with intelligent caching

## 📋 Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended) or macOS 11+
- **CPU**: 4+ cores (8+ recommended for high-frequency trading)
- **RAM**: 8GB minimum (16GB recommended for production)
- **Storage**: 50GB SSD available space (100GB+ for historical data)
- **Network**: Stable internet connection with <50ms latency to exchanges
- **Docker**: Version 24.0+ with Docker Compose v2.20+
- **Python**: 3.12+ for local development

### Kaayaan Infrastructure Services
```yaml
services:
  mongodb:
    uri: mongodb://username:password@mongodb:27017/
    database: mcp_crypto_trading
    collections: [analyses, portfolios, alerts, backtests]
    
  redis:
    uri: redis://:password@redis:6379
    databases: [0: cache, 1: sessions, 2: queues]
    
  postgresql:
    uri: postgresql://user:password@postgresql:5432/database
    purpose: n8n workflow data and user management
    
  whatsapp:
    api_url: https://your-whatsapp-api.com
    session_id: your_session_id
    purpose: Real-time trading alerts
```

### External API Requirements
- **Binance API**: Real-time OHLCV data (1200 req/min limit)
- **CoinGecko API**: Market cap and metadata (Pro plan recommended)
- **CoinMarketCap API**: Additional market metrics (10K calls/month)

## 🔧 Installation & Configuration

### 1. Environment Preparation

```bash
# Create project directory
mkdir -p /opt/mcp-crypto-trading
cd /opt/mcp-crypto-trading

# Clone the repository
git clone <repository-url> .
chmod +x *.sh

# Create necessary directories
mkdir -p logs data/mongodb data/redis backups

# Set proper ownership (for Linux)
sudo chown -R $(whoami):$(whoami) /opt/mcp-crypto-trading

# Make scripts executable
chmod +x setup_script.sh
chmod +x init_files.py

# Run initial setup
./setup_script.sh
```

### 2. Environment Configuration

Create production environment file:

```bash
cp env_example.sh .env.production
```

Edit `.env.production` with your settings:

```bash
# === MCP CRYPTO TRADING PRODUCTION CONFIG ===
# Core Application
ENVIRONMENT=production
PORT=8080
LOG_LEVEL=INFO
WORKERS=4

# API Keys (REQUIRED)
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
COINGECKO_API_KEY=your_coingecko_api_key_here
COINMARKETCAP_API_KEY=your_coinmarketcap_api_key_here

# Kaayaan Infrastructure (Pre-configured)
MONGODB_URI=mongodb://username:password@mongodb:27017/
REDIS_URL=redis://:password@redis:6379
DATABASE_URL=postgresql://user:password@postgresql:5432/database
WHATSAPP_API_URL=https://your-whatsapp-api.com
WHATSAPP_SESSION=your_session_id

# Performance & Caching
CACHE_TTL=300
MAX_CACHE_SIZE=1000
CONNECTION_POOL_SIZE=20
TIMEOUT_SECONDS=30

# Security
RATE_LIMIT_PER_MINUTE=100
MAX_CONCURRENT_REQUESTS=50
ENABLE_CORS=true
CORS_ORIGINS=["https://n8n.kaayaan.ai", "https://app.kaayaan.ai"]

# Monitoring & Alerting
HEALTH_CHECK_INTERVAL=60
ALERT_THRESHOLD_CPU=80
ALERT_THRESHOLD_MEMORY=85
LOG_RETENTION_DAYS=30

# WhatsApp Integration
WHATSAPP_API=https://your-whatsapp-api.com
WHATSAPP_SESSION=your_session_id
WHATSAPP_TIMEOUT=30
WHATSAPP_RATE_LIMIT=20

# Exchange APIs (Optional but recommended)
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_secret
COINGECKO_API_KEY=your_coingecko_key
COINMARKETCAP_API_KEY=your_cmc_key

# Security
JWT_SECRET_KEY=your-super-secure-jwt-key-here
ENCRYPTION_KEY=your-32-byte-encryption-key

# Performance & Monitoring
ENABLE_METRICS=true
METRICS_PORT=8080
MAX_CONCURRENT_REQUESTS=200
CACHE_TTL_SECONDS=300

# Trading Configuration
DEFAULT_RISK_PERCENTAGE=2.0
MAX_POSITION_SIZE_PERCENTAGE=10.0
MAX_ALERTS_PER_USER=50

# Error Tracking (Optional)
SENTRY_DSN=your_sentry_dsn_here
```

### 3. Infrastructure Validation

Test your environment configuration:

```bash
python -c "
from config.production import validate_environment_variables
import json
result = validate_environment_variables()
print(json.dumps(result, indent=2))
"
```

## 🏗️ Deployment Options

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# Check service status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f mcp-crypto-server
```

### Option 2: Standalone Python

```bash
# Install dependencies
pip install -r requirements_mcp.txt

# Run the MCP server
python mcp_crypto_server.py
```

### Option 3: Kubernetes (Advanced)

```bash
# Apply Kubernetes manifests (create these based on your cluster)
kubectl apply -f k8s/
kubectl get pods -l app=mcp-crypto-server
```

## 🔌 MCP Client Integration

### n8n Integration

1. **Install MCP Client in n8n**:
```bash
npm install @modelcontextprotocol/client
```

2. **Configure MCP Connection**:
```javascript
// n8n custom node configuration
const mcpClient = new MCPClient({
  transport: {
    type: 'stdio',
    command: 'python',
    args: ['/path/to/mcp_crypto_server.py']
  }
});

// Connect and use tools
await mcpClient.connect();
const tools = await mcpClient.listTools();
```

3. **Example n8n Workflow**:
```json
{
  "name": "Crypto Analysis Workflow",
  "nodes": [
    {
      "name": "Analyze Crypto",
      "type": "mcp-crypto-tool",
      "parameters": {
        "tool": "analyze_crypto",
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "save_analysis": true
      }
    }
  ]
}
```

### Claude Desktop Integration

Add to Claude Desktop config (`~/.claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "crypto-trading": {
      "command": "python",
      "args": ["/path/to/mcp_crypto_server.py"],
      "env": {
        "ENVIRONMENT": "production",
        "MONGODB_URI": "mongodb://username:password@mongodb:27017/",
        "REDIS_URL": "redis://:password@redis:6379"
      }
    }
  }
}
```

## 🛠️ Available MCP Tools

### 1. analyze_crypto
```bash
# Comprehensive cryptocurrency analysis
{
  "symbol": "BTCUSDT",
  "timeframe": "1h", 
  "comparison_symbol": "ETHUSDT",
  "save_analysis": true
}
```

### 2. monitor_portfolio
```bash
# Portfolio monitoring with risk assessment
{
  "portfolio_id": "my_portfolio",
  "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT"],
  "risk_level": "moderate"
}
```

### 3. detect_opportunities
```bash
# High-confidence trading opportunities
{
  "market_cap_range": "large",
  "confidence_threshold": 75,
  "max_results": 10
}
```

### 4. risk_assessment
```bash
# Position sizing and risk calculation
{
  "symbol": "BTCUSDT",
  "portfolio_value": 100000,
  "risk_percentage": 2.0,
  "entry_price": 45000,
  "stop_loss": 43000
}
```

### 5. market_scanner
```bash
# Market scanning for patterns
{
  "scan_type": "breakouts",
  "timeframe": "1h",
  "min_volume_usd": 1000000
}
```

### 6. alert_manager
```bash
# WhatsApp alert management
{
  "action": "create",
  "alert_type": "price",
  "symbol": "BTCUSDT",
  "condition": "price > 50000",
  "phone_number": "+1234567890"
}
```

### 7. historical_backtest
```bash
# Strategy backtesting
{
  "symbol": "BTCUSDT",
  "strategy": "technical_momentum",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "initial_capital": 10000
}
```

## 📊 Monitoring & Observability

### Health Checks

```bash
# Application health
curl http://localhost:8080/health

# Database connections
curl http://localhost:8080/health/deep

# Metrics endpoint
curl http://localhost:8080/metrics
```

### Grafana Dashboards

Access Grafana at `http://localhost:3000`:
- Username: `admin`
- Password: `admin_password`

Pre-configured dashboards:
- **MCP Crypto Overview**: System metrics and performance
- **Trading Analytics**: Analysis results and opportunities
- **Infrastructure Health**: Database and service status
- **Alert Analytics**: WhatsApp delivery metrics

### Log Aggregation

Access Kibana at `http://localhost:5601`:
- Index Pattern: `mcp-crypto-*`
- Default time range: Last 24 hours

Key log queries:
```
# Analysis requests
level: INFO AND message: "Starting analysis"

# Alert deliveries  
level: INFO AND message: "Alert notification sent"

# Errors
level: ERROR

# Performance metrics
message: "Tool execution" AND execution_time_ms: >1000
```

## 🔐 Security Configuration

### SSL/TLS Setup

```bash
# Generate SSL certificates
mkdir -p config/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout config/nginx/ssl/private.key \
  -out config/nginx/ssl/certificate.crt
```

### Firewall Configuration

```bash
# Allow required ports
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw allow 8080  # Metrics (internal only)
ufw deny 27017  # MongoDB (internal only)
ufw deny 6379   # Redis (internal only)
ufw deny 5432   # PostgreSQL (internal only)
```

### API Key Security

1. **Store secrets securely**:
```bash
# Using Docker secrets
echo "your_api_key" | docker secret create binance_key -
```

2. **Environment variable encryption**:
```bash
# Encrypt sensitive values
python -c "
from cryptography.fernet import Fernet
key = Fernet.generate_key()
f = Fernet(key)
encrypted = f.encrypt(b'your_secret_value')
print(f'Key: {key.decode()}')
print(f'Encrypted: {encrypted.decode()}')
"
```

## 🧪 Testing & Validation

### Run Test Suite

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/ -v -m "not integration"  # Unit tests only
pytest tests/ -v -m "integration"      # Integration tests
pytest tests/ -v -m "performance"      # Performance tests

# Generate coverage report
pytest tests/ --cov=. --cov-report=html
```

### Manual Testing

```bash
# Test MCP server directly
echo '{"method": "tools/list"}' | python mcp_crypto_server.py

# Test individual components
python -c "
import asyncio
from crypto_analyzer import CryptoAnalyzer
analyzer = CryptoAnalyzer()
result = asyncio.run(analyzer.analyze('BTCUSDT'))
print(f'Analysis completed: {result.symbol}')
"

# Test database connections
python -c "
from infrastructure.database_manager import DatabaseManager
import asyncio
# Test connection code here
"
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Failed**
```bash
# Check service status
docker-compose ps
docker-compose logs mongodb redis postgresql

# Test connection manually
mongosh "mongodb://username:password@localhost:27017/"
redis-cli -h localhost -p 6379 -a "password"
psql "postgresql://user:password@localhost:5432/database"
```

2. **WhatsApp API Issues**
```bash
# Test WhatsApp API
curl -X GET "https://your-whatsapp-api.com/api/sessions/your_session_id"

# Check session status
curl -X GET "https://your-whatsapp-api.com/api/sessions"
```

3. **Memory Issues**
```bash
# Check memory usage
docker stats mcp-crypto-trading

# Optimize memory settings
export PYTHONHASHSEED=0
export MALLOC_ARENA_MAX=2
```

4. **Performance Issues**
```bash
# Check async performance
python -c "
import asyncio
import time
# Performance testing code
"

# Monitor with htop
htop -p $(pgrep -f mcp_crypto_server)
```

### Log Analysis

```bash
# Application logs
docker-compose logs -f mcp-crypto-server | grep ERROR

# System logs
journalctl -u docker -f | grep mcp

# Database logs
docker-compose logs mongodb | tail -100
```

## 📈 Production Optimization

### Performance Tuning

1. **Database Optimization**:
```bash
# MongoDB indexes
mongosh --eval "
db.analysis_results.createIndex({symbol: 1, timestamp: -1})
db.opportunities.createIndex({confidence_score: -1})
"

# Redis memory optimization
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

2. **Application Tuning**:
```python
# In production.py
MAX_CONCURRENT_REQUESTS=500
CACHE_TTL_SECONDS=600
GC_THRESHOLD=1000
```

3. **Container Optimization**:
```yaml
# In docker-compose.yml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
```

### Scaling Strategies

1. **Horizontal Scaling**:
```bash
# Multiple server instances
docker-compose up --scale mcp-crypto-server=3
```

2. **Load Balancing**:
```nginx
# nginx.conf
upstream mcp_backend {
    server mcp-crypto-server:8080;
    server mcp-crypto-server-2:8080;
    server mcp-crypto-server-3:8080;
}
```

## 🔄 Maintenance

### Regular Tasks

1. **Database Cleanup**:
```bash
# Weekly cleanup script
python -c "
import asyncio
from infrastructure.database_manager import DatabaseManager
# Run cleanup_expired_data()
"
```

2. **Log Rotation**:
```bash
# Configure logrotate
echo '/app/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    create 0644 mcp mcp
}' > /etc/logrotate.d/mcp-crypto
```

3. **Health Monitoring**:
```bash
# Automated health checks
crontab -e
# Add: */5 * * * * curl -f http://localhost:8080/health || systemctl restart mcp-crypto
```

### Backup Strategy

```bash
# Database backups
docker exec mcp-mongodb mongodump --out /backup/$(date +%Y%m%d)
docker exec mcp-postgresql pg_dump -U n8n_user n8n_postgres_db > /backup/postgres_$(date +%Y%m%d).sql

# Configuration backups
tar -czf /backup/config_$(date +%Y%m%d).tar.gz config/ .env.production
```

## 📞 Support & Contact

For technical support and issues:

- **Documentation**: This deployment guide
- **Logs**: Check application and system logs first
- **Monitoring**: Use Grafana dashboards for system insights
- **Testing**: Run test suite to validate functionality

---

**🎯 Deployment Checklist:**

- [ ] Environment variables configured
- [ ] Database connections tested
- [ ] WhatsApp API accessible
- [ ] SSL certificates installed
- [ ] Monitoring dashboards configured
- [ ] Test suite passing
- [ ] Backup strategy implemented
- [ ] Security settings applied
- [ ] Performance optimizations enabled
- [ ] Health checks configured

**System Status: Production Ready ✅**