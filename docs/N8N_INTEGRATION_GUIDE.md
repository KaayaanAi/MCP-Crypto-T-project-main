# n8n Integration Guide - MCP Crypto Trading Server

Complete guide for integrating the MCP Crypto Trading Server with n8n workflows using the n8n-nodes-mcp package.

## 🚀 Quick Setup

### 1. Install MCP Client Node in n8n

```bash
# In your n8n installation directory
npm install n8n-nodes-mcp

# Or via n8n Community Nodes (recommended)
# Go to Settings > Community Nodes > Install
# Package name: n8n-nodes-mcp
```

### 2. Configure MCP Server Connection

#### Container Deployment (Recommended)
```json
{
  "name": "Crypto Trading Analysis",
  "transport": "stdio",
  "command": "docker",
  "args": [
    "exec", 
    "-i", 
    "kaayaan-crypto-trading", 
    "python3", 
    "/app/mcp_server_standalone.py"
  ],
  "cwd": "/",
  "timeout": 30000,
  "retries": 3
}
```

#### Direct Python Execution
```json
{
  "name": "Crypto Trading Analysis",
  "transport": "stdio", 
  "command": "python3",
  "args": ["/path/to/mcp_server_standalone.py"],
  "cwd": "/path/to/mcp-crypto-trading",
  "env": {
    "PYTHONPATH": "/path/to/mcp-crypto-trading",
    "ENVIRONMENT": "production"
  },
  "timeout": 30000
}
```

## 🛠️ Available MCP Tools

### 1. **analyze_crypto** - Advanced Technical Analysis

**Purpose**: Institutional-grade cryptocurrency analysis with Order Blocks, Fair Value Gaps, and Break of Structure detection.

**Input Schema**:
```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "comparison_symbol": "ETHUSDT",
  "save_analysis": true
}
```

**Output**: Comprehensive analysis with trend, volatility, institutional indicators, and BUY/SELL/HOLD recommendation.

### 2. **monitor_portfolio** - Real-time Portfolio Tracking

**Purpose**: Track portfolio performance with risk assessment and correlation analysis.

**Input Schema**:
```json
{
  "portfolio_id": "main_portfolio",
  "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT"],
  "risk_level": "moderate"
}
```

**Output**: Portfolio metrics, position analysis, risk scores, and recommendations.

### 3. **detect_opportunities** - AI-Powered Market Scanning

**Purpose**: Scan markets for high-confidence trading opportunities using multiple indicators.

**Input Schema**:
```json
{
  "market_cap_range": "all",
  "confidence_threshold": 75,
  "max_results": 10
}
```

**Output**: Ranked list of trading opportunities with entry/exit levels and risk-reward ratios.

### 4. **risk_assessment** - Position Sizing & Risk Management

**Purpose**: Calculate optimal position sizes using Kelly Criterion and Value-at-Risk methods.

**Input Schema**:
```json
{
  "symbol": "BTCUSDT",
  "portfolio_value": 50000,
  "risk_percentage": 2.0,
  "entry_price": 43500,
  "stop_loss": 42000
}
```

**Output**: Position size recommendations, risk metrics, and warnings.

### 5. **market_scanner** - Pattern Recognition Scanner

**Purpose**: Scan for breakouts, reversals, institutional moves, and volume surges.

**Input Schema**:
```json
{
  "scan_type": "breakouts",
  "timeframe": "1h", 
  "min_volume_usd": 1000000
}
```

**Output**: List of symbols matching scan criteria with pattern details.

### 6. **alert_manager** - WhatsApp Alert System

**Purpose**: Create, manage, and deliver trading alerts via WhatsApp integration.

**Input Schema**:
```json
{
  "action": "create",
  "alert_type": "price",
  "symbol": "BTCUSDT",
  "condition": "price > 45000",
  "phone_number": "+965XXXXXXXX"
}
```

**Output**: Alert confirmation and management status.

### 7. **historical_backtest** - Strategy Validation

**Purpose**: Test trading strategies against historical data with comprehensive metrics.

**Input Schema**:
```json
{
  "symbol": "BTCUSDT",
  "strategy": "ema_crossover",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 10000
}
```

**Output**: Backtest results with performance metrics, trade history, and equity curve.

## 📊 Example n8n Workflows

### Workflow 1: Automated Trading Signal Generator

```json
{
  "name": "Crypto Trading Signals",
  "nodes": [
    {
      "name": "Schedule Analysis",
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "triggerTimes": {
          "item": [
            {
              "hour": "*",
              "minute": "0"
            }
          ]
        }
      }
    },
    {
      "name": "Analyze BTC",
      "type": "n8n-nodes-mcp.mcp-client",
      "parameters": {
        "tool": "analyze_crypto",
        "arguments": {
          "symbol": "BTCUSDT",
          "timeframe": "1h",
          "save_analysis": true
        }
      }
    },
    {
      "name": "Check Signal Strength",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{ $json.intelligent_score }}",
              "operation": "largerEqual",
              "value2": 75
            }
          ]
        }
      }
    },
    {
      "name": "Send High Confidence Alert",
      "type": "n8n-nodes-mcp.mcp-client", 
      "parameters": {
        "tool": "alert_manager",
        "arguments": {
          "action": "create",
          "alert_type": "technical",
          "symbol": "={{ $json.symbol }}",
          "condition": "high_confidence_signal",
          "phone_number": "+965XXXXXXXX"
        }
      }
    }
  ]
}
```

### Workflow 2: Portfolio Risk Monitor

```json
{
  "name": "Portfolio Risk Monitoring",
  "nodes": [
    {
      "name": "Every 15 Minutes",
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "triggerTimes": {
          "item": [
            {
              "minute": "*/15"
            }
          ]
        }
      }
    },
    {
      "name": "Monitor Portfolio",
      "type": "n8n-nodes-mcp.mcp-client",
      "parameters": {
        "tool": "monitor_portfolio",
        "arguments": {
          "portfolio_id": "main_portfolio",
          "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT"],
          "risk_level": "moderate"
        }
      }
    },
    {
      "name": "Risk Alert Check",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{ $json.risk_metrics.portfolio_risk_score }}",
              "operation": "larger",
              "value2": 70
            }
          ]
        }
      }
    },
    {
      "name": "Send Risk Alert",
      "type": "n8n-nodes-mcp.mcp-client",
      "parameters": {
        "tool": "alert_manager", 
        "arguments": {
          "action": "create",
          "alert_type": "risk",
          "symbol": "PORTFOLIO",
          "condition": "high_risk_detected",
          "phone_number": "+965XXXXXXXX"
        }
      }
    }
  ]
}
```

### Workflow 3: Opportunity Hunter with Risk Assessment

```json
{
  "name": "Trading Opportunity Hunter",
  "nodes": [
    {
      "name": "Market Hours Trigger",
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "triggerTimes": {
          "item": [
            {
              "hour": "*/2",
              "minute": "0"
            }
          ]
        }
      }
    },
    {
      "name": "Scan for Opportunities", 
      "type": "n8n-nodes-mcp.mcp-client",
      "parameters": {
        "tool": "detect_opportunities",
        "arguments": {
          "market_cap_range": "large",
          "confidence_threshold": 80,
          "max_results": 5
        }
      }
    },
    {
      "name": "Process Each Opportunity",
      "type": "n8n-nodes-base.splitInBatches",
      "parameters": {
        "batchSize": 1
      }
    },
    {
      "name": "Risk Assessment",
      "type": "n8n-nodes-mcp.mcp-client",
      "parameters": {
        "tool": "risk_assessment", 
        "arguments": {
          "symbol": "={{ $json.symbol }}",
          "portfolio_value": 50000,
          "risk_percentage": 2.0,
          "entry_price": "={{ $json.entry_price }}",
          "stop_loss": "={{ $json.stop_loss }}"
        }
      }
    },
    {
      "name": "Filter by Risk-Reward",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{ $json.risk_reward_ratio }}",
              "operation": "largerEqual", 
              "value2": 2.0
            }
          ]
        }
      }
    },
    {
      "name": "Send Opportunity Alert",
      "type": "n8n-nodes-mcp.mcp-client",
      "parameters": {
        "tool": "alert_manager",
        "arguments": {
          "action": "create",
          "alert_type": "technical",
          "symbol": "={{ $json.symbol }}",
          "condition": "high_quality_opportunity",
          "phone_number": "+965XXXXXXXX"
        }
      }
    }
  ]
}
```

## 🔧 Configuration Templates

### MCP Client Node Configuration

Copy this configuration for your n8n MCP Client node:

```json
{
  "serverConfig": {
    "name": "crypto-trading",
    "transport": "stdio",
    "command": "docker",
    "args": [
      "exec",
      "-i", 
      "kaayaan-crypto-trading",
      "python3",
      "/app/mcp_server_standalone.py"
    ],
    "cwd": "/",
    "timeout": 30000,
    "retries": 3,
    "retryDelay": 1000,
    "env": {
      "ENVIRONMENT": "production",
      "LOG_LEVEL": "INFO",
      "TZ": "Asia/Kuwait"
    }
  },
  "toolConfig": {
    "validate_input": true,
    "timeout": 25000,
    "cache_results": true,
    "cache_ttl": 300
  }
}
```

### Environment Variables for n8n

Add these to your n8n environment:

```bash
# MCP Crypto Trading Integration
MCP_CRYPTO_SERVER_PATH=/path/to/mcp-crypto-trading
MCP_CRYPTO_CONTAINER=kaayaan-crypto-trading
MCP_CRYPTO_TIMEOUT=30000

# Optional: Pre-configure tool defaults
CRYPTO_DEFAULT_TIMEFRAME=1h
CRYPTO_DEFAULT_RISK_LEVEL=moderate
CRYPTO_DEFAULT_CONFIDENCE=70
```

## 📈 Advanced Workflow Patterns

### Pattern 1: Multi-Timeframe Analysis

```json
{
  "name": "Multi-Timeframe BTC Analysis",
  "description": "Analyze BTC across multiple timeframes for confluence",
  "nodes": [
    {
      "name": "Analyze 15m",
      "type": "n8n-nodes-mcp.mcp-client",
      "parameters": {
        "tool": "analyze_crypto",
        "arguments": {"symbol": "BTCUSDT", "timeframe": "15m"}
      }
    },
    {
      "name": "Analyze 1h", 
      "type": "n8n-nodes-mcp.mcp-client",
      "parameters": {
        "tool": "analyze_crypto",
        "arguments": {"symbol": "BTCUSDT", "timeframe": "1h"}
      }
    },
    {
      "name": "Analyze 4h",
      "type": "n8n-nodes-mcp.mcp-client", 
      "parameters": {
        "tool": "analyze_crypto",
        "arguments": {"symbol": "BTCUSDT", "timeframe": "4h"}
      }
    },
    {
      "name": "Confluence Analysis",
      "type": "n8n-nodes-base.function",
      "parameters": {
        "functionCode": "// Analyze confluence across timeframes\nconst timeframes = [\n  { tf: '15m', data: $input.first() },\n  { tf: '1h', data: $input.item(1) },\n  { tf: '4h', data: $input.item(2) }\n];\n\nconst bullishSignals = timeframes.filter(tf => tf.data.recommendation.action === 'BUY').length;\nconst bearishSignals = timeframes.filter(tf => tf.data.recommendation.action === 'SELL').length;\n\nconst confluenceScore = Math.max(bullishSignals, bearishSignals) / timeframes.length * 100;\nconst direction = bullishSignals > bearishSignals ? 'BULLISH' : 'BEARISH';\n\nreturn {\n  symbol: 'BTCUSDT',\n  confluence_score: confluenceScore,\n  direction: direction,\n  timeframes_analyzed: timeframes.map(tf => ({\n    timeframe: tf.tf,\n    recommendation: tf.data.recommendation.action,\n    confidence: tf.data.recommendation.confidence\n  })),\n  should_trade: confluenceScore >= 67 // 2 out of 3 timeframes agree\n};"
      }
    }
  ]
}
```

### Pattern 2: Portfolio Rebalancing Alert

```json
{
  "name": "Portfolio Rebalancing Alert",
  "description": "Monitor portfolio and alert when rebalancing needed",
  "trigger": "schedule:daily",
  "workflow": [
    {
      "tool": "monitor_portfolio",
      "arguments": {
        "portfolio_id": "main_portfolio",
        "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT"],
        "risk_level": "moderate"
      }
    },
    {
      "condition": "diversification_score < 60",
      "action": {
        "tool": "alert_manager",
        "arguments": {
          "action": "create",
          "alert_type": "risk",
          "symbol": "PORTFOLIO",
          "condition": "rebalancing_needed",
          "phone_number": "+965XXXXXXXX"
        }
      }
    }
  ]
}
```

## 🎯 Tool Usage Best Practices

### Input Validation

Always validate inputs before sending to MCP tools:

```javascript
// Validate symbol format
function validateSymbol(symbol) {
  return /^[A-Z]{6,12}$/.test(symbol);
}

// Validate timeframe
function validateTimeframe(timeframe) {
  return ['1m', '5m', '15m', '1h', '4h', '1d'].includes(timeframe);
}

// Example usage in n8n Function node
const symbol = $json.symbol?.toUpperCase();
if (!validateSymbol(symbol)) {
  throw new Error(`Invalid symbol format: ${symbol}`);
}
```

### Error Handling

Implement robust error handling:

```javascript
// Error handling wrapper for MCP calls
async function safeMCPCall(tool, arguments) {
  try {
    const result = await mcpClient.callTool(tool, arguments);
    return { success: true, data: result };
  } catch (error) {
    return { 
      success: false, 
      error: error.message,
      retry_suggested: error.code === 'TIMEOUT' || error.code === 'CONNECTION_ERROR'
    };
  }
}
```

### Rate Limiting Awareness

Respect MCP server rate limits (30 requests/minute):

```javascript
// Simple rate limiting in n8n workflows
const lastCall = $workflow.lastExecution?.startedAt;
const timeSinceLastCall = Date.now() - new Date(lastCall).getTime();
const minInterval = 2000; // 2 seconds between calls

if (timeSinceLastCall < minInterval) {
  await new Promise(resolve => setTimeout(resolve, minInterval - timeSinceLastCall));
}
```

## 🚨 Troubleshooting

### Common Issues

**1. MCP Server Connection Failed**
```bash
# Check container status
docker ps | grep crypto-trading

# Check logs
docker logs kaayaan-crypto-trading

# Test connection manually
docker exec -it kaayaan-crypto-trading python3 -c "print('MCP Server accessible')"
```

**2. Tool Execution Timeout**
- Increase timeout in n8n MCP Client configuration
- Check server logs for performance issues
- Verify network connectivity to Kaayaan infrastructure

**3. Invalid Tool Arguments**
- Validate input schema against tool requirements
- Check for required vs optional parameters
- Ensure data types match schema definitions

### Performance Optimization

**Caching Strategy**:
- Enable result caching for repeated analyses
- Use appropriate cache TTL based on timeframe
- Cache portfolio data for frequent monitoring

**Batch Operations**:
- Group multiple symbol analyses into single workflow
- Use n8n's batch processing for large datasets
- Implement parallel execution where possible

### Security Considerations

**API Keys**:
- Store API keys in n8n credentials store
- Never log or expose API keys in workflows
- Use read-only API permissions where possible

**Data Privacy**:
- Anonymize sensitive portfolio data
- Implement data retention policies
- Use secure channels for alert delivery

## 📞 Support & Resources

### Kaayaan Infrastructure Support
- **Infrastructure Issues**: Check Kaayaan infrastructure status
- **Database Connectivity**: Verify MongoDB/Redis/PostgreSQL connections
- **WhatsApp Integration**: Test WAHA API connectivity

### MCP Protocol Support
- **Protocol Issues**: Verify MCP 2.1.0+ compatibility
- **Stdio Transport**: Ensure proper stdio configuration
- **Tool Schema**: Validate against provided schemas

### Getting Help
1. Check MCP server health endpoint
2. Review application logs in `/app/logs/`
3. Test individual tools with simple inputs
4. Verify Kaayaan infrastructure connectivity

---

**Ready for Production** | Optimized for Kaayaan Infrastructure | MCP 2.1.0+ Compatible

*Version: 2.0.0 | Last Updated: 2025-08-31*