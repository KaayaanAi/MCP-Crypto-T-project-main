# MCP Crypto Trading Analysis - API Reference

<metadata>
purpose: Complete API documentation for MCP Crypto Trading Analysis tools
type: API
language: Python
dependencies: MCP, asyncio, aiohttp, pandas, numpy, ta
last-updated: 2024-12-19
</metadata>

<overview>
The MCP Crypto Trading Analysis system provides 7 intelligent trading tools accessible via the Model Context Protocol (MCP). These tools offer institutional-grade cryptocurrency analysis, real-time portfolio monitoring, and automated trading workflow integration.
</overview>

## MCP Server Connection

### Server Configuration
```json
{
  "name": "mcp-crypto-trading",
  "command": "python",
  "args": ["mcp_crypto_server.py"],
  "env": {
    "ENVIRONMENT": "production",
    "BINANCE_API_KEY": "your_key",
    "COINGECKO_API_KEY": "your_key"
  }
}
```

### Health Check
```json
{
  "method": "notifications/ping",
  "params": {}
}
```

## Trading Analysis Tools

<functions>

<function name="analyze_crypto">
  <signature>analyze_crypto(symbol: string, timeframe?: string, comparison_symbol?: string, save_analysis?: boolean) -> AnalysisResult</signature>
  <purpose>Perform comprehensive cryptocurrency analysis with institutional-grade indicators</purpose>
  
  <parameters>
    <param name="symbol" type="string" required="true">Trading pair symbol (e.g., BTCUSDT, ETHUSDT)</param>
    <param name="timeframe" type="string" required="false" default="1h">Analysis timeframe (1m, 5m, 15m, 1h, 4h, 1d)</param>
    <param name="comparison_symbol" type="string" required="false">Secondary symbol for comparative analysis</param>
    <param name="save_analysis" type="boolean" required="false" default="true">Save analysis results to database</param>
  </parameters>
  
  <returns>
    Comprehensive market analysis including:
    - Order Blocks detection with strength scoring
    - Fair Value Gaps identification
    - Break of Structure (BoS) and Change of Character (ChoCH) analysis
    - Volatility classification and trend analysis
    - Smart trading recommendations (BUY/SELL/HOLD)
    - Intelligent confidence scoring
  </returns>
  
  <examples>
    <example>
      <input>
        {
          "symbol": "BTCUSDT",
          "timeframe": "1h",
          "save_analysis": true
        }
      </input>
      <output>
        {
          "symbol": "BTCUSDT",
          "timestamp": "2024-12-19T10:30:00Z",
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
              "timestamp": "2024-12-19T09:00:00Z"
            }
          ],
          "fair_value_gaps": [
            {
              "upper_level": 43500.00,
              "lower_level": 43200.00,
              "type": "bullish",
              "timestamp": "2024-12-19T08:30:00Z"
            }
          ],
          "recommendation": {
            "action": "BUY",
            "confidence": 87.3,
            "reasoning": "Strong bullish trend with moderate volatility. Multiple confluence factors present."
          }
        }
      </output>
    </example>
  </examples>
  
  <errors>
    <error type="InvalidSymbol">When symbol is not found or invalid format</error>
    <error type="APIError">When external API calls fail</error>
    <error type="InsufficientData">When not enough historical data available</error>
  </errors>
</function>

<function name="monitor_portfolio">
  <signature>monitor_portfolio(portfolio_id: string, symbols: string[], risk_level?: string) -> PortfolioHealth</signature>
  <purpose>Comprehensive portfolio monitoring with real-time risk assessment</purpose>
  
  <parameters>
    <param name="portfolio_id" type="string" required="true">Unique portfolio identifier</param>
    <param name="symbols" type="array" required="true">Array of trading symbols to monitor</param>
    <param name="risk_level" type="string" required="false" default="moderate">Risk tolerance (conservative, moderate, aggressive)</param>
  </parameters>
  
  <returns>
    Portfolio health metrics including:
    - Real-time position valuations
    - Risk-adjusted performance metrics
    - Correlation analysis across holdings
    - Dynamic stop-loss recommendations
    - Portfolio rebalancing suggestions
  </returns>
  
  <examples>
    <example>
      <input>
        {
          "portfolio_id": "trading_portfolio_001",
          "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT"],
          "risk_level": "moderate"
        }
      </input>
      <output>
        {
          "portfolio_id": "trading_portfolio_001",
          "total_value": 125430.50,
          "24h_change": 3.2,
          "positions": [
            {
              "symbol": "BTCUSDT",
              "value": 75000.00,
              "weight": 59.8,
              "pnl_percent": 5.7,
              "risk_score": 0.3
            }
          ],
          "risk_metrics": {
            "portfolio_var_95": 2150.30,
            "max_drawdown": 8.2,
            "sharpe_ratio": 1.45,
            "correlation_risk": "medium"
          },
          "recommendations": [
            "Consider reducing BTC allocation to 50%",
            "Increase diversification with DeFi tokens"
          ]
        }
      </output>
    </example>
  </examples>
  
  <errors>
    <error type="PortfolioNotFound">When portfolio_id doesn't exist</error>
    <error type="InvalidRiskLevel">When risk_level is not supported</error>
  </errors>
</function>

<function name="detect_opportunities">
  <signature>detect_opportunities(market_cap_range?: string, confidence_threshold?: number, max_results?: number) -> TradingOpportunities</signature>
  <purpose>AI-powered detection of high-confidence trading opportunities across markets</purpose>
  
  <parameters>
    <param name="market_cap_range" type="string" required="false" default="all">Market cap filter (large, mid, small, all)</param>
    <param name="confidence_threshold" type="number" required="false" default="70">Minimum confidence score (0-100)</param>
    <param name="max_results" type="number" required="false" default="10">Maximum number of opportunities to return</param>
  </parameters>
  
  <returns>
    High-confidence trading opportunities including:
    - Multi-timeframe confluence analysis
    - Cross-asset arbitrage opportunities
    - Momentum breakout identification
    - Risk-adjusted opportunity scoring
  </returns>
  
  <examples>
    <example>
      <input>
        {
          "market_cap_range": "large",
          "confidence_threshold": 80,
          "max_results": 5
        }
      </input>
      <output>
        {
          "scan_timestamp": "2024-12-19T10:30:00Z",
          "opportunities": [
            {
              "symbol": "ETHUSDT",
              "opportunity_type": "breakout_momentum",
              "confidence": 85.3,
              "timeframes": ["15m", "1h", "4h"],
              "entry_price": 2456.78,
              "target_price": 2675.20,
              "stop_loss": 2234.50,
              "risk_reward_ratio": 2.8,
              "reasoning": "Triple timeframe confluence with volume surge"
            }
          ],
          "market_context": {
            "overall_sentiment": "bullish",
            "volatility": "increasing",
            "institutional_flow": "accumulation"
          }
        }
      </output>
    </example>
  </examples>
</function>

<function name="risk_assessment">
  <signature>risk_assessment(symbol: string, portfolio_value: number, entry_price: number, stop_loss: number, risk_percentage?: number) -> RiskMetrics</signature>
  <purpose>Calculate optimal position sizing and comprehensive risk metrics</purpose>
  
  <parameters>
    <param name="symbol" type="string" required="true">Trading symbol for analysis</param>
    <param name="portfolio_value" type="number" required="true">Total portfolio value in USD</param>
    <param name="entry_price" type="number" required="true">Planned entry price</param>
    <param name="stop_loss" type="number" required="true">Stop loss price level</param>
    <param name="risk_percentage" type="number" required="false" default="2.0">Risk percentage per trade (1-10)</param>
  </parameters>
  
  <returns>
    Comprehensive risk assessment including:
    - Optimal position size calculation
    - Value-at-Risk (VaR) analysis
    - Maximum Drawdown projections
    - Kelly Criterion position sizing
    - Risk-adjusted return expectations
  </returns>
  
  <examples>
    <example>
      <input>
        {
          "symbol": "BTCUSDT",
          "portfolio_value": 50000,
          "entry_price": 43500,
          "stop_loss": 41000,
          "risk_percentage": 2.0
        }
      </input>
      <output>
        {
          "symbol": "BTCUSDT",
          "risk_analysis": {
            "position_size_usd": 1000.00,
            "position_size_units": 0.02299,
            "risk_amount": 1000.00,
            "reward_potential": 2800.00,
            "risk_reward_ratio": 2.8
          },
          "var_analysis": {
            "var_95_daily": 125.50,
            "var_99_daily": 187.30,
            "expected_shortfall": 234.20
          },
          "kelly_criterion": {
            "optimal_fraction": 0.035,
            "recommended_size": 0.025,
            "max_safe_size": 0.05
          },
          "warnings": []
        }
      </output>
    </example>
  </examples>
</function>

<function name="market_scanner">
  <signature>market_scanner(scan_type?: string, timeframe?: string, min_volume_usd?: number) -> MarketScanResults</signature>
  <purpose>Automated scanning for breakouts, reversals, and institutional market moves</purpose>
  
  <parameters>
    <param name="scan_type" type="string" required="false" default="all">Scan type (breakouts, reversals, institutional, volume_surge, all)</param>
    <param name="timeframe" type="string" required="false" default="1h">Analysis timeframe</param>
    <param name="min_volume_usd" type="number" required="false" default="1000000">Minimum 24h volume filter</param>
  </parameters>
  
  <returns>
    Market scanning results including:
    - Top gainers and losers with analysis
    - Volume anomaly detection
    - Technical pattern identification
    - Institutional flow detection
    - Sector rotation analysis
  </returns>
  
  <examples>
    <example>
      <input>
        {
          "scan_type": "breakouts",
          "timeframe": "1h",
          "min_volume_usd": 5000000
        }
      </input>
      <output>
        {
          "scan_timestamp": "2024-12-19T10:30:00Z",
          "scan_type": "breakouts",
          "results": [
            {
              "symbol": "SOLUSDT",
              "pattern": "ascending_triangle_breakout",
              "confidence": 78.5,
              "volume_surge": 245.6,
              "price_change_24h": 12.3,
              "breakout_price": 85.67,
              "target_price": 94.20,
              "volume_profile": "institutional_accumulation"
            }
          ],
          "market_summary": {
            "breakouts_detected": 12,
            "reversals_detected": 8,
            "institutional_moves": 3,
            "overall_sentiment": "bullish"
          }
        }
      </output>
    </example>
  </examples>
</function>

<function name="alert_manager">
  <signature>alert_manager(action: string, alert_type?: string, symbol?: string, condition?: string, phone_number?: string) -> AlertResponse</signature>
  <purpose>Configure and manage intelligent trading alerts via WhatsApp integration</purpose>
  
  <parameters>
    <param name="action" type="string" required="true">Alert action (create, update, delete, list)</param>
    <param name="alert_type" type="string" required="false">Alert type (price, technical, volume, news)</param>
    <param name="symbol" type="string" required="false">Trading symbol for alert</param>
    <param name="condition" type="string" required="false">Alert trigger condition</param>
    <param name="phone_number" type="string" required="false">WhatsApp number for notifications</param>
  </parameters>
  
  <returns>
    Alert management results including:
    - Alert creation/modification confirmation
    - Active alert list and status
    - Delivery status and history
    - Alert performance metrics
  </returns>
  
  <examples>
    <example>
      <input>
        {
          "action": "create",
          "alert_type": "price",
          "symbol": "BTCUSDT",
          "condition": "price > 45000",
          "phone_number": "+97150XXXXXXX"
        }
      </input>
      <output>
        {
          "alert_id": "alert_001_btc_price",
          "status": "created",
          "alert_details": {
            "symbol": "BTCUSDT",
            "type": "price",
            "condition": "price > 45000",
            "current_price": 43420.50,
            "distance_to_trigger": 3.6
          },
          "delivery_settings": {
            "whatsapp_number": "+97150XXXXXXX",
            "delivery_confirmed": true,
            "test_message_sent": true
          },
          "message": "Alert created successfully and will trigger when BTC price exceeds $45,000"
        }
      </output>
    </example>
  </examples>
</function>

<function name="historical_backtest">
  <signature>historical_backtest(symbol: string, strategy: string, start_date: string, end_date: string, initial_capital?: number) -> BacktestResults</signature>
  <purpose>Test trading strategies against historical data with comprehensive performance metrics</purpose>
  
  <parameters>
    <param name="symbol" type="string" required="true">Trading symbol for backtesting</param>
    <param name="strategy" type="string" required="true">Strategy configuration (JSON string)</param>
    <param name="start_date" type="string" required="true">Backtest start date (YYYY-MM-DD)</param>
    <param name="end_date" type="string" required="true">Backtest end date (YYYY-MM-DD)</param>
    <param name="initial_capital" type="number" required="false" default="10000">Starting capital in USD</param>
  </parameters>
  
  <returns>
    Comprehensive backtest results including:
    - Strategy performance metrics
    - Risk-adjusted returns analysis
    - Maximum drawdown periods
    - Win/loss ratios and statistics
    - Monte Carlo simulations
    - Optimal parameter recommendations
  </returns>
  
  <examples>
    <example>
      <input>
        {
          "symbol": "BTCUSDT",
          "strategy": "{\"name\":\"order_block_reversal\",\"timeframe\":\"1h\",\"risk_percent\":2}",
          "start_date": "2024-01-01",
          "end_date": "2024-12-01",
          "initial_capital": 10000
        }
      </input>
      <output>
        {
          "strategy_name": "order_block_reversal",
          "backtest_period": {
            "start_date": "2024-01-01",
            "end_date": "2024-12-01",
            "duration_days": 335
          },
          "performance_metrics": {
            "total_return": 45.7,
            "annualized_return": 49.8,
            "max_drawdown": -12.3,
            "sharpe_ratio": 1.87,
            "sortino_ratio": 2.34,
            "calmar_ratio": 4.05
          },
          "trade_statistics": {
            "total_trades": 127,
            "winning_trades": 78,
            "losing_trades": 49,
            "win_rate": 61.4,
            "avg_win": 3.2,
            "avg_loss": -1.8,
            "profit_factor": 1.76
          },
          "final_capital": 14570.45,
          "recommendations": [
            "Consider increasing position size during high-confidence setups",
            "Optimize stop-loss levels for better risk management"
          ]
        }
      </output>
    </example>
  </examples>
</function>

</functions>

## Error Handling

<patterns>
<pattern name="standard-error-response">
All tools return standardized error responses:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error description",
    "details": {
      "tool": "tool_name",
      "timestamp": "2024-12-19T10:30:00Z",
      "request_id": "uuid"
    }
  }
}
```
</pattern>

<pattern name="retry-logic">
For API failures, implement exponential backoff:
```python
async def retry_api_call(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```
</pattern>
</patterns>

## Rate Limiting & Performance

### API Rate Limits
- **Binance API**: 1200 requests/minute
- **CoinGecko API**: 50 calls/minute (free), 500/minute (pro)  
- **CoinMarketCap API**: 333 calls/day (free)

### Optimization Strategies
- **Caching**: 5-minute cache for analysis results
- **Batch Processing**: Combine multiple symbol requests
- **Connection Pooling**: Reuse HTTP connections
- **Async Processing**: Non-blocking I/O operations

### Performance Benchmarks
- **analyze_crypto**: ~200-500ms average response
- **market_scanner**: ~1-3s for full market scan
- **backtest**: ~5-30s depending on period length

## Integration Examples

### n8n MCP Client Integration
```javascript
// n8n MCP Client Node Configuration
{
  "server": "mcp-crypto-trading",
  "tool": "analyze_crypto",
  "arguments": {
    "symbol": "{{ $json.trading_pair }}",
    "timeframe": "1h"
  }
}
```

### Python Direct Integration
```python
import asyncio
from mcp_crypto_server import MCPCryptoServer

async def analyze_market():
    server = MCPCryptoServer()
    await server.initialize()
    
    result = await server._handle_analyze_crypto({
        "symbol": "BTCUSDT",
        "timeframe": "1h"
    })
    
    return result[0].text
```

### REST API Wrapper
```python
# Create REST endpoint for MCP tools
from fastapi import FastAPI
from mcp_crypto_server import MCPCryptoServer

app = FastAPI()
server = MCPCryptoServer()

@app.post("/analyze/{symbol}")
async def analyze(symbol: str, timeframe: str = "1h"):
    result = await server._handle_analyze_crypto({
        "symbol": symbol,
        "timeframe": timeframe
    })
    return json.loads(result[0].text)
```

## Security Considerations

### API Key Management
- Store keys in secure environment variables
- Use read-only permissions where possible
- Rotate keys regularly (quarterly)
- Monitor for unusual API usage patterns

### Data Privacy
- No sensitive data logged
- User positions encrypted in transit
- Database connections secured with TLS
- Regular security audits performed

### Access Control
- Rate limiting per client
- IP whitelisting for production
- Request signing for critical operations
- Audit logging for all trades

---

**Production-Grade Trading Intelligence API**  
*Last Updated: December 2024 | Version: 1.0.0*

For integration support, contact: api-support@kaayaan.ai