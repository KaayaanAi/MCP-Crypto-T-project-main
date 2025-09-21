# API Documentation - MCP Crypto Trading Analysis Server

<metadata>
purpose: Complete API reference for MCP Crypto Trading Analysis Server
type: API
language: Python
dependencies: mcp==1.14.1, fastapi==0.112.0, pydantic==2.8.2
last-updated: 2025-09-21
version: 2.0.0
protocol: MCP 2.1.0+
</metadata>

<overview>
The MCP Crypto Trading Analysis Server provides 7 intelligent trading tools via MCP protocol with stdio transport. All tools support real-time cryptocurrency analysis, portfolio monitoring, and trading intelligence with enterprise-grade security and validation.
</overview>

## Protocol Information

| Specification | Details |
|---------------|---------|
| **Protocol** | MCP (Model Context Protocol) 2.1.0+ |
| **Transport** | stdio (standard input/output) |
| **Format** | JSON-RPC with MCP extensions |
| **Authentication** | Environment-based API keys |
| **Rate Limiting** | 60 requests/minute per tool |
| **Validation** | Comprehensive input sanitization |

---

## Server Connection

### MCP Client Configuration
```json
{
  "mcpServers": {
    "crypto-trading": {
      "command": "python",
      "args": ["mcp_server_standalone.py"],
      "cwd": "/path/to/mcp-crypto-trading",
      "env": {
        "BINANCE_API_KEY": "your_binance_key",
        "BINANCE_SECRET_KEY": "your_binance_secret",
        "COINGECKO_API_KEY": "your_coingecko_key"
      }
    }
  }
}
```

### Health Check
```bash
# Test server connectivity
echo '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | python mcp_server_standalone.py
```

---

## Authentication & Security

### API Keys Configuration
```bash
# Required environment variables
export BINANCE_API_KEY="your_binance_api_key"
export BINANCE_SECRET_KEY="your_binance_secret_key"
export COINGECKO_API_KEY="your_coingecko_api_key"
export COINMARKETCAP_API_KEY="your_coinmarketcap_key"

# Optional infrastructure
export MONGODB_URI="mongodb://localhost:27017/crypto_trading"
export REDIS_URL="redis://localhost:6379"
export DATABASE_URL="postgresql://user:pass@localhost/trading"
```

### Security Features
- **Input Validation:** XSS, SQL injection, path traversal protection
- **Rate Limiting:** 60 requests/minute per tool with exponential backoff
- **Sanitization:** All user inputs sanitized and validated
- **Logging:** Comprehensive audit trails with request tracking
- **Error Handling:** Secure error messages without information leakage

---

<functions>

<function name="analyze_crypto">
  <signature>analyze_crypto(symbol: str, timeframe: str = "1h", save_analysis: bool = false) -> CryptoAnalysis</signature>
  <purpose>Advanced institutional-grade cryptocurrency market analysis with order blocks, fair value gaps, and intelligent scoring</purpose>
  <parameters>
    <param name="symbol" type="string" required="true" pattern="^[A-Z]{2,10}USDT?$">Trading pair symbol (e.g., BTCUSDT, ETHUSDT)</param>
    <param name="timeframe" type="string" required="false" enum="['1m','5m','15m','30m','1h','4h','1d','1w']">Chart timeframe for analysis</param>
    <param name="save_analysis" type="boolean" required="false">Whether to save analysis results to database</param>
  </parameters>
  <returns>Comprehensive market analysis with trend, volatility, order blocks, fair value gaps, and BUY/SELL/HOLD recommendation</returns>
  <examples>
    <example>
      <input>{"symbol": "BTCUSDT", "timeframe": "1h", "save_analysis": true}</input>
      <output>{
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "timestamp": "2025-09-21T10:00:00Z",
        "analysis": {
          "trend": "bullish_strong",
          "volatility": "moderate",
          "confidence": 87.3,
          "intelligent_score": 1.34
        },
        "order_blocks": [
          {
            "level": 43250.50,
            "type": "demand",
            "strength": 85.2,
            "timestamp": "2025-09-21T09:00:00Z"
          }
        ],
        "fair_value_gaps": [
          {
            "upper": 43500.00,
            "lower": 43300.00,
            "gap_size": 200.00,
            "timeframe": "1h"
          }
        ],
        "recommendation": {
          "action": "BUY",
          "confidence": 87.3,
          "reasoning": "Strong bullish trend with moderate volatility, order block support at 43250"
        },
        "technical_indicators": {
          "rsi": 65.2,
          "macd": 145.67,
          "bollinger_position": "upper",
          "volume_profile": "high"
        }
      }</output>
    </example>
  </examples>
  <errors>
    <error type="ValidationError">Invalid symbol format or unsupported timeframe</error>
    <error type="APIError">Exchange API unavailable or rate limited</error>
    <error type="DataError">Insufficient market data for analysis</error>
  </errors>
</function>

<function name="monitor_portfolio">
  <signature>monitor_portfolio(positions: List[Position], risk_tolerance: str = "moderate") -> PortfolioMonitoring</signature>
  <purpose>Real-time portfolio health monitoring with position-by-position risk assessment and optimization suggestions</purpose>
  <parameters>
    <param name="positions" type="array" required="true">Array of position objects with symbol, size, entry_price, and optional stop_loss/take_profit</param>
    <param name="risk_tolerance" type="string" required="false" enum="['conservative','moderate','aggressive']">Risk management approach</param>
  </parameters>
  <returns>Portfolio health metrics, position analysis, risk assessment, and optimization recommendations</returns>
  <examples>
    <example>
      <input>{
        "positions": [
          {"symbol": "BTCUSDT", "size": 1.5, "entry_price": 42000, "stop_loss": 40000},
          {"symbol": "ETHUSDT", "size": 10, "entry_price": 2500, "take_profit": 3000}
        ],
        "risk_tolerance": "moderate"
      }</input>
      <output>{
        "portfolio_health": {
          "overall_score": 78.5,
          "total_value": 127500.00,
          "unrealized_pnl": 4250.00,
          "risk_score": 0.35
        },
        "position_analysis": [
          {
            "symbol": "BTCUSDT",
            "current_price": 43500.00,
            "unrealized_pnl": 2250.00,
            "pnl_percentage": 5.36,
            "risk_level": "low",
            "suggestions": ["Consider taking partial profits", "Trailing stop at 42500"]
          }
        ],
        "risk_metrics": {
          "portfolio_var": 2150.75,
          "max_drawdown": 0.08,
          "sharpe_ratio": 1.42,
          "correlation_matrix": {"BTCUSDT-ETHUSDT": 0.73}
        },
        "recommendations": [
          "Reduce position correlation",
          "Consider rebalancing BTC position",
          "Add stop-loss to ETH position"
        ]
      }</output>
    </example>
  </examples>
  <errors>
    <error type="ValidationError">Invalid position format or missing required fields</error>
    <error type="CalculationError">Insufficient data for risk calculations</error>
  </errors>
</function>

<function name="detect_opportunities">
  <signature>detect_opportunities(scan_type: str = "breakout_momentum", min_volume: float = 1000000, timeframes: List[str] = ["15m", "1h"]) -> TradingOpportunities</signature>
  <purpose>AI-powered market scanning for high-confidence trading opportunities with multi-timeframe analysis</purpose>
  <parameters>
    <param name="scan_type" type="string" required="false" enum="['breakout_momentum','reversal_patterns','arbitrage','volatility_expansion']">Type of opportunities to scan for</param>
    <param name="min_volume" type="number" required="false" minimum="100000">Minimum 24h volume filter</param>
    <param name="timeframes" type="array" required="false">Timeframes for confluence analysis</param>
  </parameters>
  <returns>Ranked list of trading opportunities with confidence scores and entry/exit strategies</returns>
  <examples>
    <example>
      <input>{
        "scan_type": "breakout_momentum",
        "min_volume": 1000000,
        "timeframes": ["15m", "1h", "4h"]
      }</input>
      <output>{
        "scan_timestamp": "2025-09-21T10:15:00Z",
        "opportunities": [
          {
            "symbol": "ADAUSDT",
            "opportunity_type": "breakout_momentum",
            "confidence": 89.2,
            "current_price": 0.4250,
            "entry_strategy": {
              "entry_price": 0.4280,
              "stop_loss": 0.4150,
              "take_profit": 0.4600,
              "risk_reward": 2.46
            },
            "timeframe_confluence": {
              "15m": "bullish_breakout",
              "1h": "volume_spike",
              "4h": "support_retest"
            },
            "technical_reasons": [
              "Triangle breakout with volume",
              "RSI momentum confirmation",
              "Order block support below"
            ]
          }
        ],
        "market_overview": {
          "total_scanned": 150,
          "opportunities_found": 8,
          "average_confidence": 72.4
        }
      }</output>
    </example>
  </examples>
  <errors>
    <error type="ValidationError">Invalid scan type or timeframe parameters</error>
    <error type="MarketError">Market data unavailable for scanning</error>
  </errors>
</function>

<function name="risk_assessment">
  <signature>risk_assessment(portfolio_value: float, positions: List[Position], market_conditions: str = "normal") -> RiskAssessment</signature>
  <purpose>Comprehensive risk management with VaR calculations, position sizing, and portfolio optimization</purpose>
  <parameters>
    <param name="portfolio_value" type="number" required="true" minimum="1000">Total portfolio value in USD</param>
    <param name="positions" type="array" required="true">Current positions for risk analysis</param>
    <param name="market_conditions" type="string" required="false" enum="['bull','bear','sideways','volatile','normal']">Current market regime</param>
  </parameters>
  <returns>Detailed risk metrics, position sizing recommendations, and portfolio optimization suggestions</returns>
  <examples>
    <example>
      <input>{
        "portfolio_value": 100000,
        "positions": [
          {"symbol": "BTCUSDT", "size": 2.0, "entry_price": 42000}
        ],
        "market_conditions": "volatile"
      }</input>
      <output>{
        "risk_metrics": {
          "portfolio_var_1d": 2850.50,
          "portfolio_var_7d": 8950.25,
          "max_drawdown": 0.12,
          "volatility": 0.048,
          "beta": 1.23
        },
        "position_sizing": {
          "recommended_max_position": 0.05,
          "current_risk_exposure": 0.84,
          "suggested_rebalancing": [
            {"symbol": "BTCUSDT", "action": "reduce", "target_weight": 0.60}
          ]
        },
        "risk_alerts": [
          "Portfolio concentration too high",
          "Consider hedging in volatile conditions",
          "Add stable assets for diversification"
        ]
      }</output>
    </example>
  </examples>
  <errors>
    <error type="ValidationError">Invalid portfolio value or position data</error>
    <error type="CalculationError">Insufficient historical data for risk calculations</error>
  </errors>
</function>

<function name="market_scanner">
  <signature>market_scanner(scan_criteria: str = "volume_breakout", market_cap_min: float = 100000000, limit: int = 20) -> MarketScan</signature>
  <purpose>Automated market surveillance for pattern detection, anomalies, and trading signals across cryptocurrency markets</purpose>
  <parameters>
    <param name="scan_criteria" type="string" required="false" enum="['volume_breakout','price_divergence','technical_patterns','momentum_shift','volatility_spike']">Scanning criteria type</param>
    <param name="market_cap_min" type="number" required="false" minimum="10000000">Minimum market capitalization filter</param>
    <param name="limit" type="integer" required="false" minimum="5" maximum="100">Maximum number of results to return</param>
  </parameters>
  <returns>Ranked list of market signals with technical analysis and actionable insights</returns>
  <examples>
    <example>
      <input>{
        "scan_criteria": "volume_breakout",
        "market_cap_min": 500000000,
        "limit": 10
      }</input>
      <output>{
        "scan_results": [
          {
            "symbol": "DOGEUSDT",
            "signal_type": "volume_breakout",
            "signal_strength": 8.7,
            "current_price": 0.0925,
            "volume_increase": 340.5,
            "technical_score": 82.1,
            "pattern_details": {
              "breakout_level": 0.0920,
              "resistance_levels": [0.0950, 0.1000],
              "support_levels": [0.0900, 0.0850]
            }
          }
        ],
        "market_summary": {
          "total_analyzed": 200,
          "signals_found": 15,
          "average_strength": 7.2,
          "market_sentiment": "bullish"
        }
      }</output>
    </example>
  </examples>
  <errors>
    <error type="ValidationError">Invalid scan criteria or parameter ranges</error>
    <error type="DataError">Insufficient market data for comprehensive scanning</error>
  </errors>
</function>

<function name="alert_manager">
  <signature>alert_manager(alert_type: str, conditions: Dict, notification_channels: List[str] = ["console"]) -> AlertResponse</signature>
  <purpose>Intelligent alert management system for price thresholds, technical indicators, and portfolio events</purpose>
  <parameters>
    <param name="alert_type" type="string" required="true" enum="['price_threshold','technical_indicator','portfolio_event','risk_warning']">Type of alert to create</param>
    <param name="conditions" type="object" required="true">Alert conditions and parameters</param>
    <param name="notification_channels" type="array" required="false">Delivery channels for alerts</param>
  </parameters>
  <returns>Alert configuration confirmation and tracking information</returns>
  <examples>
    <example>
      <input>{
        "alert_type": "price_threshold",
        "conditions": {
          "symbol": "BTCUSDT",
          "price_above": 45000,
          "price_below": 40000
        },
        "notification_channels": ["console", "whatsapp"]
      }</input>
      <output>{
        "alert_id": "alert_btc_threshold_20250921_001",
        "status": "active",
        "created_at": "2025-09-21T10:30:00Z",
        "conditions_summary": "BTC price above $45,000 or below $40,000",
        "monitoring_status": "active",
        "estimated_delivery_time": "< 30 seconds"
      }</output>
    </example>
  </examples>
  <errors>
    <error type="ValidationError">Invalid alert type or condition parameters</error>
    <error type="NotificationError">Notification channel unavailable</error>
  </errors>
</function>

<function name="historical_backtest">
  <signature>historical_backtest(strategy: Dict, symbol: str, start_date: str, end_date: str, initial_capital: float = 10000) -> BacktestResults</signature>
  <purpose>Strategy validation engine with historical performance analysis, risk metrics, and optimization recommendations</purpose>
  <parameters>
    <param name="strategy" type="object" required="true">Trading strategy parameters and rules</param>
    <param name="symbol" type="string" required="true" pattern="^[A-Z]{2,10}USDT?$">Trading pair for backtesting</param>
    <param name="start_date" type="string" required="true" pattern="^\d{4}-\d{2}-\d{2}$">Start date in YYYY-MM-DD format</param>
    <param name="end_date" type="string" required="true" pattern="^\d{4}-\d{2}-\d{2}$">End date in YYYY-MM-DD format</param>
    <param name="initial_capital" type="number" required="false" minimum="1000">Starting capital for backtest</param>
  </parameters>
  <returns>Comprehensive backtest results with performance metrics, trade analysis, and strategy optimization suggestions</returns>
  <examples>
    <example>
      <input>{
        "strategy": {
          "type": "moving_average_crossover",
          "fast_ma": 10,
          "slow_ma": 30,
          "stop_loss": 0.02,
          "take_profit": 0.06
        },
        "symbol": "BTCUSDT",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "initial_capital": 10000
      }</input>
      <output>{
        "backtest_summary": {
          "total_return": 0.234,
          "annual_return": 0.234,
          "sharpe_ratio": 1.67,
          "max_drawdown": 0.085,
          "win_rate": 0.68,
          "total_trades": 47
        },
        "performance_metrics": {
          "final_capital": 12340.75,
          "total_fees": 234.50,
          "best_trade": 890.25,
          "worst_trade": -156.75
        },
        "risk_analysis": {
          "volatility": 0.045,
          "var_95": 450.75,
          "calmar_ratio": 2.75
        },
        "optimization_suggestions": [
          "Consider increasing stop-loss to 2.5%",
          "Fast MA of 8 may improve performance",
          "Add volume filter for better entries"
        ]
      }</output>
    </example>
  </examples>
  <errors>
    <error type="ValidationError">Invalid strategy parameters or date format</error>
    <error type="DataError">Insufficient historical data for the specified period</error>
    <error type="CalculationError">Strategy parameters result in invalid backtest</error>
  </errors>
</function>

</functions>

---

## Rate Limiting & Error Handling

### Rate Limits
| Resource | Limit | Window | Behavior |
|----------|-------|--------|----------|
| **Per Tool** | 60 requests | 1 minute | HTTP 429 with retry-after header |
| **Global Server** | 300 requests | 1 minute | Exponential backoff applied |
| **Data APIs** | Varies by provider | See provider docs | Cached responses when possible |

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid symbol format",
    "details": {
      "field": "symbol",
      "provided": "btc",
      "expected": "BTCUSDT format"
    },
    "request_id": "req_20250921_103045_abc123"
  }
}
```

### Common Error Codes
| Code | Description | Resolution |
|------|-------------|------------|
| `VALIDATION_ERROR` | Invalid input parameters | Check parameter format and constraints |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Wait for rate limit reset |
| `API_KEY_INVALID` | Authentication failed | Verify API keys in environment |
| `INSUFFICIENT_DATA` | Not enough market data | Try different timeframe or symbol |
| `MARKET_CLOSED` | Exchange unavailable | Check exchange status |

---

## Performance & Optimization

### Caching Strategy
- **Analysis Results:** 5-minute TTL for active markets
- **Market Data:** 1-minute TTL for price data
- **Historical Data:** 1-hour TTL for backtesting
- **Portfolio Calculations:** 30-second TTL for real-time monitoring

### Response Times (Production)
| Tool | Typical Response | 95th Percentile |
|------|------------------|-----------------|
| `analyze_crypto` | 200-400ms | 800ms |
| `monitor_portfolio` | 150-300ms | 600ms |
| `detect_opportunities` | 500-1000ms | 2000ms |
| `market_scanner` | 800-1500ms | 3000ms |
| `risk_assessment` | 300-600ms | 1200ms |
| `alert_manager` | 100-200ms | 400ms |
| `historical_backtest` | 1000-5000ms | 10000ms |

### Optimization Tips
1. **Use caching** - Avoid repeated requests for same parameters
2. **Batch requests** - Combine multiple symbol analysis when possible
3. **Choose appropriate timeframes** - Higher timeframes process faster
4. **Limit historical ranges** - Smaller date ranges for backtesting
5. **Monitor rate limits** - Implement exponential backoff

---

## Integration Examples

### Python MCP Client
```python
import json
import subprocess

def call_mcp_tool(tool_name, arguments):
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": 1
    }

    process = subprocess.Popen(
        ["python", "mcp_server_standalone.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    stdout, stderr = process.communicate(json.dumps(request))
    return json.loads(stdout)

# Example usage
result = call_mcp_tool("analyze_crypto", {
    "symbol": "BTCUSDT",
    "timeframe": "1h"
})
```

### n8n Workflow Node
```json
{
  "name": "Crypto Analysis",
  "type": "mcp-client",
  "parameters": {
    "server": "crypto-trading",
    "tool": "analyze_crypto",
    "arguments": {
      "symbol": "{{ $json.symbol }}",
      "timeframe": "1h",
      "save_analysis": true
    }
  }
}
```

### TypeScript Client
```typescript
interface MCPRequest {
  jsonrpc: string;
  method: string;
  params: {
    name: string;
    arguments: Record<string, any>;
  };
  id: number;
}

async function analyzeCrypto(symbol: string, timeframe: string = "1h") {
  const request: MCPRequest = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "analyze_crypto",
      arguments: { symbol, timeframe }
    },
    id: Date.now()
  };

  // Send via your MCP client implementation
  return await mcpClient.send(request);
}
```

---

## WebSocket API (Enterprise)

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/crypto');

ws.onopen = function() {
    // Subscribe to real-time updates
    ws.send(JSON.stringify({
        action: 'subscribe',
        symbols: ['BTCUSDT', 'ETHUSDT'],
        types: ['price', 'analysis']
    }));
};
```

### Real-time Events
```json
{
  "event": "price_update",
  "symbol": "BTCUSDT",
  "price": 43567.89,
  "change_24h": 2.34,
  "timestamp": "2025-09-21T10:45:00Z"
}
```

---

## Environment Configuration

### Required Variables
```bash
# Exchange API Keys (Required)
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
COINGECKO_API_KEY=your_coingecko_api_key
COINMARKETCAP_API_KEY=your_coinmarketcap_key

# Database Configuration (Optional)
MONGODB_URI=mongodb://localhost:27017/crypto_trading
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://user:pass@localhost/trading

# Notification Settings (Optional)
WHATSAPP_SESSION=your_session_id
SLACK_WEBHOOK_URL=your_slack_webhook
TELEGRAM_BOT_TOKEN=your_telegram_token

# Performance Settings (Optional)
CACHE_TTL=300
RATE_LIMIT_PER_MINUTE=60
MAX_CONCURRENT_REQUESTS=10
```

### Development vs Production
```bash
# Development
export ENVIRONMENT=development
export LOG_LEVEL=DEBUG
export CACHE_ENABLED=false

# Production
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export CACHE_ENABLED=true
export MONITORING_ENABLED=true
```

---

## Monitoring & Observability

### Health Check Endpoint
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime": 3600,
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "exchanges": "healthy"
  }
}
```

### Metrics Endpoint
```bash
curl http://localhost:8000/metrics
```

### Structured Logging
```json
{
  "timestamp": "2025-09-21T10:30:00Z",
  "level": "INFO",
  "logger": "mcp-crypto-server",
  "message": "Tool executed successfully",
  "tool": "analyze_crypto",
  "symbol": "BTCUSDT",
  "execution_time": 245,
  "request_id": "req_20250921_103000_xyz789"
}
```

---

*For deployment instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)*
*For security information, see [SECURITY_AUDIT_REPORT.md](SECURITY_AUDIT_REPORT.md)*
*For version history, see [CHANGELOG.md](CHANGELOG.md)*