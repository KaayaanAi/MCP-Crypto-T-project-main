# Production Deployment Guide - MCP Crypto Trading Server

**Production-ready MCP module for Kaayaan infrastructure with complete Docker orchestration and n8n integration.**

---

## 🎯 Project Overview

**MCP Crypto Trading Server v2.1.0** - Advanced cryptocurrency trading analysis platform with institutional-grade indicators, real-time portfolio monitoring, and seamless n8n workflow integration.

### Auto-Detected Project Configuration
- **Project Name**: `crypto-trading` (auto-detected from folder)
- **Container Name**: `kaayaan-crypto-trading`
- **MCP Protocol**: stdio (MCP 2.1.0+ compliant)
- **Infrastructure**: Full Kaayaan integration

### Core Capabilities
✅ **7 Intelligent MCP Tools** - All production-ready and tested
✅ **Institutional Indicators** - Order Blocks, Fair Value Gaps, Break of Structure
✅ **Real-time Portfolio Monitoring** - Risk assessment and correlation analysis  
✅ **AI-Powered Opportunity Detection** - Multi-timeframe confluence analysis
✅ **WhatsApp Alert Integration** - Instant notifications via WAHA API
✅ **Historical Backtesting** - Strategy validation with comprehensive metrics
✅ **Production Infrastructure** - MongoDB, Redis, PostgreSQL integration

---

## 🚀 Quick Deployment (2 Minutes)

### Option 1: Instant Docker Deployment (Recommended)

```bash
# 1. Navigate to project directory
cd /Users/aiagentkuwait/mcp-all/MCP-Crypto-T-project-main

# 2. Configure environment (one-time setup)
cp .env.production.example .env.production
# Edit .env.production with your API keys

# 3. Start server (fully automated)
./start_mcp_server.sh docker

# 4. Verify deployment
docker logs kaayaan-crypto-trading
```

### Option 2: Direct Python Execution

```bash
# 1. Start with full validation
./start_mcp_server.sh python

# 2. Or skip validation for faster startup
./start_mcp_server.sh python --no-test --no-deps
```

### Option 3: Manual Docker Compose

```bash
# Build and deploy manually
docker-compose -f docker-compose.kaayaan.yml up -d

# Check status
docker ps | grep crypto-trading
```

---

## 🏗️ Infrastructure Integration

### Kaayaan Infrastructure Connections (Pre-configured)

| Service | Connection | Purpose |
|---------|------------|---------|
| **MongoDB** | `mongodb://username:password@mongodb:27017/database` | Trade data and analysis storage |
| **Redis** | `redis://:password@redis:6379` | High-performance caching and session management |
| **PostgreSQL** | `postgresql://user:password@postgresql:5432/database` | n8n workflow data and user management |
| **WhatsApp API** | `https://your-whatsapp-api.com` (Session: your_session_id) | Real-time alert delivery system |

### Network Integration

The server automatically connects to the existing `kaayaan_default` Docker network for seamless integration with your infrastructure.

---

## 🔧 n8n Workflow Integration

### Install MCP Client Node

```bash
# In n8n installation
npm install n8n-nodes-mcp

# Or via n8n UI: Settings > Community Nodes > Install: n8n-nodes-mcp
```

### Configure MCP Connection

Use this configuration in your n8n MCP Client node:

```json
{
  "serverConfig": {
    "name": "crypto-trading",
    "transport": "stdio",
    "command": "docker",
    "args": ["exec", "-i", "kaayaan-crypto-trading", "python3", "/app/mcp_server_standalone.py"],
    "timeout": 30000
  }
}
```

### Ready-to-Use Tool Configurations

Copy `n8n_mcp_config.json` into your n8n MCP Client node for instant access to all 7 trading tools with proper validation schemas.

---

## 🛠️ MCP Tools Reference

### 1. **analyze_crypto** - Advanced Market Analysis
```json
{
  "tool": "analyze_crypto",
  "arguments": {
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "save_analysis": true
  }
}
```
**Returns**: Institutional indicators, trend analysis, volatility assessment, BUY/SELL/HOLD recommendation with confidence scoring.

### 2. **monitor_portfolio** - Portfolio Health Tracking  
```json
{
  "tool": "monitor_portfolio",
  "arguments": {
    "portfolio_id": "main_portfolio",
    "symbols": ["BTCUSDT", "ETHUSDT"],
    "risk_level": "moderate"
  }
}
```
**Returns**: Portfolio metrics, position analysis, risk scores, diversification assessment, and rebalancing recommendations.

### 3. **detect_opportunities** - Market Opportunity Scanner
```json
{
  "tool": "detect_opportunities", 
  "arguments": {
    "market_cap_range": "large",
    "confidence_threshold": 75,
    "max_results": 10
  }
}
```
**Returns**: High-confidence trading opportunities with entry/exit levels, risk-reward ratios, and supporting analysis.

### 4. **risk_assessment** - Position Sizing Calculator
```json
{
  "tool": "risk_assessment",
  "arguments": {
    "symbol": "BTCUSDT",
    "portfolio_value": 50000,
    "entry_price": 43500,
    "stop_loss": 42000
  }
}
```
**Returns**: Optimal position sizing using Kelly Criterion, VaR calculations, and risk warnings.

### 5. **market_scanner** - Pattern Recognition
```json
{
  "tool": "market_scanner",
  "arguments": {
    "scan_type": "breakouts",
    "timeframe": "1h",
    "min_volume_usd": 1000000
  }
}
```
**Returns**: Symbols matching pattern criteria with technical setup details.

### 6. **alert_manager** - WhatsApp Notifications
```json
{
  "tool": "alert_manager",
  "arguments": {
    "action": "create", 
    "alert_type": "price",
    "symbol": "BTCUSDT",
    "condition": "price > 45000",
    "phone_number": "+965XXXXXXXX"
  }
}
```
**Returns**: Alert configuration status and delivery confirmation.

### 7. **historical_backtest** - Strategy Validation
```json
{
  "tool": "historical_backtest",
  "arguments": {
    "symbol": "BTCUSDT",
    "strategy": "institutional_breakout",
    "start_date": "2024-01-01", 
    "end_date": "2024-12-31"
  }
}
```
**Returns**: Complete backtest results with performance metrics, trade history, and equity curve analysis.

---

## 📊 Performance & Monitoring

### Resource Usage (Optimized for Kaayaan Hardware)
- **Memory**: 512MB reserved, 2GB limit
- **CPU**: 0.5 core reserved, 1.0 core limit  
- **Network**: Integrated with `kaayaan_default`
- **Storage**: Persistent volumes for data, logs, cache

### Health Monitoring
```bash
# Check infrastructure health
docker exec kaayaan-crypto-trading python3 -c "
import asyncio
from infrastructure.kaayaan_factory import quick_health_check
health = asyncio.run(quick_health_check())
print(f'MongoDB: {health.mongodb_status}')
print(f'Redis: {health.redis_status}') 
print(f'PostgreSQL: {health.postgres_status}')
print(f'WhatsApp: {health.whatsapp_status}')
"

# Monitor container resources
docker stats kaayaan-crypto-trading

# View logs
docker logs -f kaayaan-crypto-trading
```

### Rate Limiting & Caching
- **Rate Limit**: 30 requests/minute per tool (configurable)
- **Caching**: Redis-based with 5-minute TTL for analysis results
- **Optimization**: Intelligent request batching and connection pooling

---

## 🔐 Security & Configuration

### Environment Variables (Required)

**API Keys** (Add to `.env.production`):
```bash
# Binance API (Required for real-time data)
BINANCE_API_KEY=your_actual_api_key
BINANCE_SECRET_KEY=your_actual_secret_key

# CoinGecko API (Optional - enhances market data)
COINGECKO_API_KEY=your_coingecko_key

# CoinMarketCap API (Optional)
COINMARKETCAP_API_KEY=your_cmc_key
```

### Security Features
✅ **Input Validation** - All inputs validated against schemas
✅ **Rate Limiting** - Prevents API abuse and resource exhaustion
✅ **Error Recovery** - Graceful handling of API failures and network issues
✅ **Audit Logging** - Complete request/response logging for compliance
✅ **Non-root Container** - Runs as `mcpuser` for enhanced security

---

## 🎛️ Management Commands

### Container Management
```bash
# Start server
./start_mcp_server.sh docker

# Stop server
docker stop kaayaan-crypto-trading

# Restart server
docker restart kaayaan-crypto-trading

# Update server (rebuild with latest code)
docker-compose -f docker-compose.kaayaan.yml build --no-cache
docker-compose -f docker-compose.kaayaan.yml up -d
```

### Troubleshooting
```bash
# Check container logs
docker logs kaayaan-crypto-trading

# Interactive container access
docker exec -it kaayaan-crypto-trading /bin/bash

# Test MCP server manually
docker exec -i kaayaan-crypto-trading python3 /app/mcp_server_standalone.py

# Infrastructure health check
./start_mcp_server.sh python --no-deps --no-validate
```

### Performance Tuning
```bash
# Monitor resource usage
docker stats kaayaan-crypto-trading

# Adjust container limits (edit docker-compose.kaayaan.yml)
# memory: 2G -> 4G (for high-frequency analysis)
# cpus: '1.0' -> '2.0' (for parallel processing)

# Clear cache if needed
docker exec kaayaan-crypto-trading redis-cli -h redis FLUSHDB
```

---

## 📋 Production Checklist

### Pre-Deployment
- [ ] Copy `.env.production.example` to `.env.production`
- [ ] Configure API keys (Binance, CoinGecko, CoinMarketCap)  
- [ ] Verify Kaayaan infrastructure is running
- [ ] Test infrastructure connectivity: `./start_mcp_server.sh --no-deps python`

### Deployment
- [ ] Build Docker image: `docker build -f Dockerfile.production -t kaayaan/mcp-crypto-trading:2.1.0 .`
- [ ] Start container: `docker-compose -f docker-compose.kaayaan.yml up -d`
- [ ] Verify container health: `docker ps | grep crypto-trading`
- [ ] Test MCP tools: Use n8n MCP Client node with simple analysis

### Post-Deployment
- [ ] Configure n8n MCP Client with provided configuration
- [ ] Set up monitoring alerts for container health
- [ ] Configure log rotation and backup policies
- [ ] Test WhatsApp alert delivery
- [ ] Validate rate limiting and performance

### Ongoing Operations
- [ ] Monitor daily logs in `/app/logs/`
- [ ] Check weekly infrastructure health reports
- [ ] Review monthly performance metrics
- [ ] Update API keys before expiration
- [ ] Backup analysis data and configurations

---

## 🚨 Emergency Procedures

### Server Unresponsive
```bash
# 1. Check container status
docker ps | grep crypto-trading

# 2. Check logs for errors
docker logs --tail=100 kaayaan-crypto-trading

# 3. Restart container
docker restart kaayaan-crypto-trading

# 4. If restart fails, rebuild
docker-compose -f docker-compose.kaayaan.yml down
docker-compose -f docker-compose.kaayaan.yml up -d --build
```

### Infrastructure Connectivity Issues
```bash
# Test individual services
docker exec kaayaan-crypto-trading python3 -c "
import asyncio
from infrastructure.kaayaan_factory import KaayaanInfrastructureFactory

async def test():
    factory = KaayaanInfrastructureFactory()
    await factory.initialize()
    health = await factory.health_check()
    print(health)
    await factory.cleanup()

asyncio.run(test())
"
```

### Data Recovery
```bash
# Check data volumes
docker volume ls | grep crypto

# Backup current data
docker run --rm -v crypto_trading_data:/data -v $(pwd):/backup alpine tar czf /backup/crypto_data_backup_$(date +%Y%m%d).tar.gz /data

# Restore from backup
docker run --rm -v crypto_trading_data:/data -v $(pwd):/backup alpine tar xzf /backup/crypto_data_backup_YYYYMMDD.tar.gz -C /
```

---

## 🎉 Success Validation

After deployment, verify everything works:

1. **Container Health**: `docker ps | grep crypto-trading` shows "Up" status
2. **Infrastructure**: All Kaayaan services respond to health checks
3. **MCP Tools**: n8n MCP Client can successfully call `analyze_crypto` tool
4. **Alerts**: WhatsApp alert delivery works via `alert_manager` tool
5. **Performance**: Response times < 5 seconds for analysis tools

---

## 📞 Production Support

### Kaayaan Infrastructure Support
- **MongoDB Issues**: Check connection pool settings and authentication
- **Redis Performance**: Monitor cache hit rates and connection counts
- **PostgreSQL**: Verify n8n database connectivity and query performance
- **WhatsApp Integration**: Test WAHA API session and message delivery

### Application Support
- **MCP Protocol**: Ensure stdio transport configuration is correct
- **Tool Errors**: Check input validation and API rate limiting
- **Performance**: Monitor CPU/memory usage and adjust container limits

---

**🏆 DEPLOYMENT COMPLETE**

Your MCP Crypto Trading Server is now production-ready with:
- ✅ Full Kaayaan infrastructure integration
- ✅ Container orchestration with Docker Compose
- ✅ n8n workflow automation capability
- ✅ WhatsApp alert delivery system
- ✅ Comprehensive monitoring and health checks
- ✅ Enterprise-grade security and performance optimization

**Container Name**: `kaayaan-crypto-trading`  
**n8n Integration**: Ready with provided configuration  
**Infrastructure**: Connected to Kaayaan MongoDB, Redis, PostgreSQL  
**Alerts**: WhatsApp delivery via WhatsApp API (Session: your_session_id)

*Ready for immediate production use with institutional-grade cryptocurrency trading analysis.*