# MCP Crypto Trading Analysis - n8n Integration Guide

<metadata>
purpose: Complete n8n workflow integration guide for MCP Crypto Trading platform
type: integration
language: JavaScript/JSON
dependencies: n8n, MCP Client Node, webhook triggers, HTTP nodes
last-updated: 2024-12-19
</metadata>

<overview>
This guide provides comprehensive n8n workflow integration for the MCP Crypto Trading Analysis platform. It includes ready-to-use workflow templates, advanced automation patterns, and best practices for professional trading operations.
</overview>

## n8n MCP Client Setup

### Installing MCP Client Node

```bash
# Install n8n MCP Client node (community node)
npm install n8n-nodes-mcp-client

# Or install via n8n UI
# Settings > Community Nodes > Install: n8n-nodes-mcp-client
```

### MCP Server Configuration

<configuration name="mcp_server_config">
  <server_type>stdio</server_type>
  <connection_params>
    {
      "name": "mcp-crypto-trading",
      "command": "python",
      "args": ["/opt/mcp-crypto-trading/mcp_crypto_server.py"],
      "cwd": "/opt/mcp-crypto-trading",
      "env": {
        "ENVIRONMENT": "production",
        "BINANCE_API_KEY": "{{ $env.BINANCE_API_KEY }}",
        "COINGECKO_API_KEY": "{{ $env.COINGECKO_API_KEY }}",
        "COINMARKETCAP_API_KEY": "{{ $env.COINMARKETCAP_API_KEY }}"
      }
    }
  </connection_params>
</configuration>

### Basic MCP Client Node Configuration

```json
{
  "server": "mcp-crypto-trading",
  "tool": "analyze_crypto",
  "arguments": {
    "symbol": "{{ $json.symbol }}",
    "timeframe": "{{ $json.timeframe || '1h' }}",
    "save_analysis": true
  },
  "continueOnFail": false,
  "retryOnFail": true,
  "maxRetries": 3
}
```

## Core Trading Workflows

### 1. Basic Market Analysis Workflow

<workflow name="basic_market_analysis">
  <description>Analyze cryptocurrency and send results via webhook</description>
  
  ```json
  {
    "name": "Basic Crypto Analysis",
    "nodes": [
      {
        "name": "Webhook Trigger",
        "type": "n8n-nodes-base.webhook",
        "parameters": {
          "path": "crypto-analysis",
          "httpMethod": "POST",
          "responseMode": "responseNode"
        }
      },
      {
        "name": "Validate Input",
        "type": "n8n-nodes-base.function",
        "parameters": {
          "functionCode": "if (!$input.first().json.symbol) {\n  throw new Error('Symbol is required');\n}\nif (!$input.first().json.symbol.includes('USDT')) {\n  items[0].json.symbol += 'USDT';\n}\nreturn $input.all();"
        }
      },
      {
        "name": "Analyze Crypto",
        "type": "n8n-nodes-mcp-client",
        "parameters": {
          "server": "mcp-crypto-trading",
          "tool": "analyze_crypto",
          "arguments": {
            "symbol": "{{ $json.symbol }}",
            "timeframe": "{{ $json.timeframe || '1h' }}",
            "save_analysis": true
          }
        }
      },
      {
        "name": "Format Response",
        "type": "n8n-nodes-base.function",
        "parameters": {
          "functionCode": "const analysis = JSON.parse($json.result);\nreturn [{\n  json: {\n    symbol: analysis.symbol,\n    recommendation: analysis.recommendation,\n    confidence: analysis.analysis.confidence,\n    timestamp: new Date().toISOString(),\n    analysis_url: `https://app.kaayaan.ai/analysis/${analysis.symbol}`\n  }\n}];"
        }
      },
      {
        "name": "Webhook Response",
        "type": "n8n-nodes-base.respondToWebhook",
        "parameters": {
          "respondWith": "json",
          "responseBody": "={{ $json }}"
        }
      }
    ],
    "connections": {
      "Webhook Trigger": {
        "main": [["Validate Input"]]
      },
      "Validate Input": {
        "main": [["Analyze Crypto"]]
      },
      "Analyze Crypto": {
        "main": [["Format Response"]]
      },
      "Format Response": {
        "main": [["Webhook Response"]]
      }
    }
  }
  ```
</workflow>

### 2. Advanced Trading Signal Workflow

<workflow name="advanced_trading_signals">
  <description>Multi-timeframe analysis with risk assessment and WhatsApp alerts</description>
  
  ```json
  {
    "name": "Advanced Trading Signals",
    "nodes": [
      {
        "name": "Schedule Trigger",
        "type": "n8n-nodes-base.cron",
        "parameters": {
          "rule": {
            "minute": "0,15,30,45",
            "hour": "*"
          }
        }
      },
      {
        "name": "Define Symbols",
        "type": "n8n-nodes-base.function",
        "parameters": {
          "functionCode": "const symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT'];\nreturn symbols.map(symbol => ({ json: { symbol } }));"
        }
      },
      {
        "name": "Multi-Timeframe Analysis",
        "type": "n8n-nodes-base.splitInBatches",
        "parameters": {
          "batchSize": 1
        }
      },
      {
        "name": "15m Analysis",
        "type": "n8n-nodes-mcp-client",
        "parameters": {
          "server": "mcp-crypto-trading",
          "tool": "analyze_crypto",
          "arguments": {
            "symbol": "{{ $json.symbol }}",
            "timeframe": "15m",
            "save_analysis": true
          }
        }
      },
      {
        "name": "1h Analysis", 
        "type": "n8n-nodes-mcp-client",
        "parameters": {
          "server": "mcp-crypto-trading",
          "tool": "analyze_crypto",
          "arguments": {
            "symbol": "{{ $json.symbol }}",
            "timeframe": "1h", 
            "save_analysis": true
          }
        }
      },
      {
        "name": "4h Analysis",
        "type": "n8n-nodes-mcp-client", 
        "parameters": {
          "server": "mcp-crypto-trading",
          "tool": "analyze_crypto",
          "arguments": {
            "symbol": "{{ $json.symbol }}",
            "timeframe": "4h",
            "save_analysis": true
          }
        }
      },
      {
        "name": "Confluence Check",
        "type": "n8n-nodes-base.function",
        "parameters": {
          "functionCode": "const analyses = $input.all();\nconst symbol = analyses[0].json.symbol;\n\nconst timeframes = {\n  '15m': JSON.parse(analyses.find(a => a.json.timeframe === '15m')?.json.result || '{}'),\n  '1h': JSON.parse(analyses.find(a => a.json.timeframe === '1h')?.json.result || '{}'),\n  '4h': JSON.parse(analyses.find(a => a.json.timeframe === '4h')?.json.result || '{}')\n};\n\n// Check for confluence\nconst recommendations = Object.values(timeframes).map(tf => tf.recommendation?.action);\nconst bullishCount = recommendations.filter(r => r === 'BUY').length;\nconst bearishCount = recommendations.filter(r => r === 'SELL').length;\n\nconst confluence = {\n  symbol,\n  timeframes,\n  confluence_score: Math.max(bullishCount, bearishCount),\n  signal: bullishCount >= 2 ? 'STRONG_BUY' : bearishCount >= 2 ? 'STRONG_SELL' : 'NEUTRAL',\n  confidence: Math.max(...Object.values(timeframes).map(tf => tf.analysis?.confidence || 0))\n};\n\n// Only proceed with high-confidence signals\nif (confluence.confluence_score >= 2 && confluence.confidence > 75) {\n  return [{ json: confluence }];\n}\n\nreturn [];"
        }
      },
      {
        "name": "Risk Assessment",
        "type": "n8n-nodes-mcp-client",
        "parameters": {
          "server": "mcp-crypto-trading", 
          "tool": "risk_assessment",
          "arguments": {
            "symbol": "{{ $json.symbol }}",
            "portfolio_value": 10000,
            "entry_price": "{{ $json.timeframes['1h'].current_price }}",
            "stop_loss": "{{ $json.signal === 'STRONG_BUY' ? ($json.timeframes['1h'].current_price * 0.95) : ($json.timeframes['1h'].current_price * 1.05) }}",
            "risk_percentage": 2.0
          }
        }
      },
      {
        "name": "Send WhatsApp Alert",
        "type": "n8n-nodes-mcp-client",
        "parameters": {
          "server": "mcp-crypto-trading",
          "tool": "alert_manager", 
          "arguments": {
            "action": "create",
            "alert_type": "technical",
            "symbol": "{{ $json.symbol }}",
            "condition": "Multi-timeframe confluence detected",
            "phone_number": "+97150XXXXXXX"
          }
        }
      }
    ],
    "connections": {
      "Schedule Trigger": {
        "main": [["Define Symbols"]]
      },
      "Define Symbols": {
        "main": [["Multi-Timeframe Analysis"]]
      },
      "Multi-Timeframe Analysis": {
        "main": [["15m Analysis", "1h Analysis", "4h Analysis"]]
      },
      "15m Analysis": {
        "main": [["Confluence Check"]]
      },
      "1h Analysis": {
        "main": [["Confluence Check"]]  
      },
      "4h Analysis": {
        "main": [["Confluence Check"]]
      },
      "Confluence Check": {
        "main": [["Risk Assessment"]]
      },
      "Risk Assessment": {
        "main": [["Send WhatsApp Alert"]]
      }
    }
  }
  ```
</workflow>

### 3. Portfolio Monitoring Dashboard

<workflow name="portfolio_dashboard">
  <description>Real-time portfolio monitoring with automated rebalancing alerts</description>
  
  ```json
  {
    "name": "Portfolio Monitor Dashboard",
    "nodes": [
      {
        "name": "Schedule Trigger",
        "type": "n8n-nodes-base.cron", 
        "parameters": {
          "rule": {
            "minute": "*/5",
            "hour": "*"
          }
        }
      },
      {
        "name": "Get Portfolio Config",
        "type": "n8n-nodes-base.function",
        "parameters": {
          "functionCode": "return [{\n  json: {\n    portfolio_id: 'main_trading_portfolio',\n    symbols: ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT'],\n    risk_level: 'moderate',\n    target_allocations: {\n      'BTCUSDT': 40,\n      'ETHUSDT': 25, \n      'ADAUSDT': 15,\n      'SOLUSDT': 10,\n      'DOTUSDT': 10\n    }\n  }\n}];"
        }
      },
      {
        "name": "Monitor Portfolio",
        "type": "n8n-nodes-mcp-client",
        "parameters": {
          "server": "mcp-crypto-trading",
          "tool": "monitor_portfolio", 
          "arguments": {
            "portfolio_id": "{{ $json.portfolio_id }}",
            "symbols": "{{ $json.symbols }}",
            "risk_level": "{{ $json.risk_level }}"
          }
        }
      },
      {
        "name": "Parse Portfolio Data",
        "type": "n8n-nodes-base.function",
        "parameters": {
          "functionCode": "const portfolio = JSON.parse($json.result);\nconst config = $input.first().json;\n\n// Calculate allocation drift\nconst allocations = {};\nportfolio.positions.forEach(pos => {\n  allocations[pos.symbol] = pos.weight;\n});\n\nconst drifts = {};\nlet maxDrift = 0;\nObject.keys(config.target_allocations).forEach(symbol => {\n  const target = config.target_allocations[symbol];\n  const actual = allocations[symbol] || 0;\n  const drift = Math.abs(actual - target);\n  drifts[symbol] = { target, actual, drift };\n  maxDrift = Math.max(maxDrift, drift);\n});\n\nreturn [{\n  json: {\n    portfolio,\n    drifts,\n    maxDrift,\n    needsRebalancing: maxDrift > 5,\n    riskAlert: portfolio.risk_metrics.portfolio_var_95 > 5000\n  }\n}];"
        }
      },
      {
        "name": "Check Alerts",
        "type": "n8n-nodes-base.if",
        "parameters": {
          "conditions": {\n    \"boolean\": [\n      {\n        \"value1\": \"={{ $json.needsRebalancing }}\",\n        \"value2\": true\n      }\n    ]\n  }\n}"
        }
      },
      {
        "name": "Send Rebalancing Alert",
        "type": "n8n-nodes-mcp-client",
        "parameters": {
          "server": "mcp-crypto-trading",
          "tool": "alert_manager",
          "arguments": {
            "action": "create",
            "alert_type": "portfolio",
            "symbol": "PORTFOLIO",
            "condition": "Portfolio drift exceeded 5%",
            "phone_number": "+97150XXXXXXX"
          }
        }
      },
      {
        "name": "Update Dashboard",
        "type": "n8n-nodes-base.httpRequest",
        "parameters": {
          "url": "https://app.kaayaan.ai/api/portfolio/update",
          "method": "POST",
          "body": {
            "portfolio_data": "={{ $json.portfolio }}",
            "alerts": "={{ $json.needsRebalancing ? ['REBALANCING_NEEDED'] : [] }}"
          },
          "headers": {
            "Authorization": "Bearer {{ $env.KAAYAAN_API_TOKEN }}",
            "Content-Type": "application/json"
          }
        }
      }
    ],
    "connections": {
      "Schedule Trigger": {
        "main": [["Get Portfolio Config"]]
      },
      "Get Portfolio Config": {
        "main": [["Monitor Portfolio"]]
      },
      "Monitor Portfolio": {
        "main": [["Parse Portfolio Data"]]
      },
      "Parse Portfolio Data": {
        "main": [["Check Alerts", "Update Dashboard"]]
      },
      "Check Alerts": {
        "main": [["Send Rebalancing Alert"], []]
      }
    }
  }
  ```
</workflow>

### 4. Automated Market Scanner

<workflow name="market_scanner_automation">
  <description>Continuous market scanning for breakout opportunities</description>
  
  ```json
  {
    "name": "Market Scanner Bot",
    "nodes": [
      {
        "name": "High-Frequency Scanner",
        "type": "n8n-nodes-base.cron",
        "parameters": {
          "rule": {
            "minute": "*/2",
            "hour": "0-23"
          }
        }
      },
      {
        "name": "Market Scan",
        "type": "n8n-nodes-mcp-client",
        "parameters": {
          "server": "mcp-crypto-trading",
          "tool": "market_scanner",
          "arguments": {
            "scan_type": "all",
            "timeframe": "15m",
            "min_volume_usd": 5000000
          }
        }
      },
      {
        "name": "Filter High-Confidence Opportunities",
        "type": "n8n-nodes-base.function",
        "parameters": {
          "functionCode": "const scanResults = JSON.parse($json.result);\nconst opportunities = scanResults.results || [];\n\n// Filter for high-confidence opportunities\nconst filtered = opportunities.filter(opp => {\n  return opp.confidence > 80 && \n         opp.volume_surge > 200 &&\n         ['breakout_momentum', 'institutional_accumulation'].includes(opp.pattern);\n});\n\nif (filtered.length === 0) {\n  return [];\n}\n\nreturn filtered.map(opp => ({ json: opp }));"
        }
      },
      {
        "name": "Detailed Analysis",
        "type": "n8n-nodes-mcp-client",
        "parameters": {
          "server": "mcp-crypto-trading",
          "tool": "analyze_crypto",
          "arguments": {
            "symbol": "{{ $json.symbol }}",
            "timeframe": "1h",
            "save_analysis": true
          }
        }
      },
      {
        "name": "Risk Assessment",
        "type": "n8n-nodes-mcp-client",
        "parameters": {
          "server": "mcp-crypto-trading",
          "tool": "risk_assessment", 
          "arguments": {
            "symbol": "{{ $json.symbol }}",
            "portfolio_value": 50000,
            "entry_price": "{{ $json.breakout_price }}",
            "stop_loss": "{{ $json.breakout_price * 0.92 }}",
            "risk_percentage": 1.5
          }
        }
      },
      {
        "name": "Create Trading Alert",
        "type": "n8n-nodes-base.function",
        "parameters": {
          "functionCode": "const opportunity = $input.all()[0].json;\nconst analysis = JSON.parse($input.all()[1].json.result);\nconst riskAssessment = JSON.parse($input.all()[2].json.result);\n\nconst alert = {\n  symbol: opportunity.symbol,\n  pattern: opportunity.pattern,\n  confidence: opportunity.confidence,\n  entry_price: opportunity.breakout_price,\n  target_price: opportunity.target_price,\n  stop_loss: riskAssessment.risk_analysis.stop_loss,\n  position_size: riskAssessment.risk_analysis.position_size_usd,\n  risk_reward: riskAssessment.risk_analysis.risk_reward_ratio,\n  analysis_summary: analysis.recommendation.reasoning,\n  timestamp: new Date().toISOString()\n};\n\nreturn [{ json: alert }];"
        }
      },
      {
        "name": "Send High-Priority Alert",
        "type": "n8n-nodes-mcp-client",
        "parameters": {
          "server": "mcp-crypto-trading",
          "tool": "alert_manager",
          "arguments": {
            "action": "create",
            "alert_type": "technical",
            "symbol": "{{ $json.symbol }}",
            "condition": "High-confidence breakout detected", 
            "phone_number": "+97150XXXXXXX"
          }
        }
      },
      {
        "name": "Log to Trading Journal",
        "type": "n8n-nodes-base.httpRequest",
        "parameters": {
          "url": "https://app.kaayaan.ai/api/trading-journal",
          "method": "POST",
          "body": "={{ $json }}",
          "headers": {
            "Authorization": "Bearer {{ $env.KAAYAAN_API_TOKEN }}",
            "Content-Type": "application/json"
          }
        }
      }
    ],
    "connections": {
      "High-Frequency Scanner": {
        "main": [["Market Scan"]]
      },
      "Market Scan": {
        "main": [["Filter High-Confidence Opportunities"]]
      },
      "Filter High-Confidence Opportunities": {
        "main": [["Detailed Analysis"]]
      },
      "Detailed Analysis": {
        "main": [["Risk Assessment"]]
      },
      "Risk Assessment": {
        "main": [["Create Trading Alert"]]
      },
      "Create Trading Alert": {
        "main": [["Send High-Priority Alert", "Log to Trading Journal"]]
      }
    }
  }
  ```
</workflow>

## Advanced Integration Patterns

### Error Handling and Retry Logic

<pattern name="robust_error_handling">
  ```json
  {
    "name": "Error Handling Node",
    "type": "n8n-nodes-base.function",
    "parameters": {
      "functionCode": "try {\n  // MCP tool call with retry logic\n  let retries = 3;\n  let result;\n  \n  for (let i = 0; i < retries; i++) {\n    try {\n      result = await $execute('mcp-crypto-trading', 'analyze_crypto', {\n        symbol: $json.symbol,\n        timeframe: $json.timeframe\n      });\n      break;\n    } catch (error) {\n      if (i === retries - 1) throw error;\n      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));\n    }\n  }\n  \n  return [{ json: { success: true, result } }];\n  \n} catch (error) {\n  // Log error and create fallback response\n  console.error('MCP tool failed:', error.message);\n  \n  return [{\n    json: {\n      success: false,\n      error: error.message,\n      fallback_action: 'use_cached_data',\n      timestamp: new Date().toISOString()\n    }\n  }];\n}"
    }
  }
  ```
</pattern>

### Batch Processing for Multiple Symbols

<pattern name="batch_processing">
  ```json
  {
    "name": "Batch Symbol Processor",
    "type": "n8n-nodes-base.function", 
    "parameters": {
      "functionCode": "const symbols = $json.symbols || [];\nconst batchSize = 5;\nconst batches = [];\n\nfor (let i = 0; i < symbols.length; i += batchSize) {\n  batches.push(symbols.slice(i, i + batchSize));\n}\n\nconst results = [];\nfor (const batch of batches) {\n  const batchPromises = batch.map(symbol => \n    $execute('mcp-crypto-trading', 'analyze_crypto', {\n      symbol,\n      timeframe: '1h',\n      save_analysis: true\n    })\n  );\n  \n  const batchResults = await Promise.all(batchPromises);\n  results.push(...batchResults);\n  \n  // Rate limiting - wait between batches\n  if (batches.indexOf(batch) < batches.length - 1) {\n    await new Promise(resolve => setTimeout(resolve, 2000));\n  }\n}\n\nreturn results.map(result => ({ json: result }));"
    }
  }
  ```
</pattern>

### Dynamic Configuration Management

<pattern name="dynamic_config">
  ```json
  {
    "name": "Config Manager",
    "type": "n8n-nodes-base.function",
    "parameters": {
      "functionCode": "// Load configuration from external source\nconst configResponse = await $httpRequest({\n  url: 'https://app.kaayaan.ai/api/trading-config',\n  method: 'GET',\n  headers: {\n    'Authorization': 'Bearer {{ $env.KAAYAAN_API_TOKEN }}'\n  }\n});\n\nconst config = configResponse.data;\n\n// Apply configuration to workflow execution\nconst workflowConfig = {\n  risk_percentage: config.risk_settings.default_risk_percent,\n  symbols_to_monitor: config.active_symbols,\n  alert_thresholds: config.alert_settings,\n  timeframes: config.analysis_timeframes,\n  portfolio_settings: config.portfolio_management\n};\n\nreturn [{ json: workflowConfig }];"
    }
  }
  ```
</pattern>

## Performance Optimization

### Caching Strategies

<optimization name="result_caching">
  ```json
  {
    "name": "Cached Analysis",
    "type": "n8n-nodes-base.function",
    "parameters": {
      "functionCode": "const cacheKey = `analysis_${$json.symbol}_${$json.timeframe}`;\nconst cacheExpiry = 300000; // 5 minutes\n\n// Check cache first\nconst cached = $workflow.getStaticData('cache')[cacheKey];\nif (cached && (Date.now() - cached.timestamp) < cacheExpiry) {\n  return [{ json: { cached: true, result: cached.data } }];\n}\n\n// Cache miss - fetch fresh data\nconst result = await $execute('mcp-crypto-trading', 'analyze_crypto', {\n  symbol: $json.symbol,\n  timeframe: $json.timeframe\n});\n\n// Store in cache\nif (!$workflow.getStaticData('cache')) {\n  $workflow.setStaticData('cache', {});\n}\n$workflow.getStaticData('cache')[cacheKey] = {\n  data: result,\n  timestamp: Date.now()\n};\n\nreturn [{ json: { cached: false, result } }];"
    }
  }
  ```
</optimization>

### Parallel Execution Optimization

<optimization name="parallel_processing">
  ```json
  {
    "name": "Parallel MCP Calls",
    "type": "n8n-nodes-base.function",
    "parameters": {
      "functionCode": "const symbol = $json.symbol;\n\n// Execute multiple MCP tools in parallel\nconst parallelCalls = await Promise.allSettled([\n  $execute('mcp-crypto-trading', 'analyze_crypto', {\n    symbol,\n    timeframe: '1h'\n  }),\n  $execute('mcp-crypto-trading', 'risk_assessment', {\n    symbol,\n    portfolio_value: 10000,\n    entry_price: $json.current_price,\n    stop_loss: $json.current_price * 0.95\n  }),\n  $execute('mcp-crypto-trading', 'detect_opportunities', {\n    market_cap_range: 'large',\n    confidence_threshold: 75\n  })\n]);\n\n// Process results\nconst results = {\n  analysis: parallelCalls[0].status === 'fulfilled' ? parallelCalls[0].value : null,\n  risk_assessment: parallelCalls[1].status === 'fulfilled' ? parallelCalls[1].value : null,\n  opportunities: parallelCalls[2].status === 'fulfilled' ? parallelCalls[2].value : null,\n  errors: parallelCalls.filter(r => r.status === 'rejected').map(r => r.reason)\n};\n\nreturn [{ json: results }];"
    }
  }
  ```
</optimization>

## Monitoring and Debugging

### Workflow Health Monitoring

<monitoring name="health_check">
  ```json
  {
    "name": "Workflow Health Check",
    "nodes": [
      {
        "name": "Health Check Trigger",
        "type": "n8n-nodes-base.cron",
        "parameters": {
          "rule": {
            "minute": "*/10",
            "hour": "*"
          }
        }
      },
      {
        "name": "Test MCP Connection",
        "type": "n8n-nodes-mcp-client",
        "parameters": {
          "server": "mcp-crypto-trading",
          "tool": "analyze_crypto",
          "arguments": {
            "symbol": "BTCUSDT",
            "timeframe": "1h"
          }
        }
      },
      {
        "name": "Validate Response",
        "type": "n8n-nodes-base.function", 
        "parameters": {
          "functionCode": "const result = JSON.parse($json.result || '{}');\nconst isHealthy = result.symbol === 'BTCUSDT' && result.analysis;\n\nconst healthStatus = {\n  timestamp: new Date().toISOString(),\n  status: isHealthy ? 'healthy' : 'unhealthy',\n  response_time: $json.execution_time,\n  details: isHealthy ? 'MCP server responding normally' : 'MCP server issues detected'\n};\n\nif (!isHealthy) {\n  // Trigger alert for unhealthy status\n  throw new Error('MCP server health check failed');\n}\n\nreturn [{ json: healthStatus }];"
        }
      }
    ]
  }
  ```
</monitoring>

### Performance Metrics Collection

<monitoring name="performance_metrics">
  ```json
  {
    "name": "Performance Tracker",
    "type": "n8n-nodes-base.function",
    "parameters": {
      "functionCode": "const startTime = Date.now();\nconst result = await $execute('mcp-crypto-trading', 'analyze_crypto', $json);\nconst endTime = Date.now();\n\nconst metrics = {\n  tool: 'analyze_crypto',\n  symbol: $json.symbol,\n  timeframe: $json.timeframe,\n  execution_time_ms: endTime - startTime,\n  timestamp: new Date().toISOString(),\n  success: !!result,\n  memory_usage: process.memoryUsage()\n};\n\n// Send to monitoring system\nawait $httpRequest({\n  url: 'https://app.kaayaan.ai/api/metrics',\n  method: 'POST',\n  body: metrics,\n  headers: {\n    'Authorization': 'Bearer {{ $env.KAAYAAN_API_TOKEN }}'\n  }\n});\n\nreturn [{ json: { result, metrics } }];"
    }
  }
  ```
</monitoring>

## Security Best Practices

### API Key Management

<security name="secure_api_keys">
  ```json
  {
    "name": "Secure Key Rotation",
    "type": "n8n-nodes-base.function",
    "parameters": {
      "functionCode": "// Check API key expiration\nconst keyExpiry = new Date($env.BINANCE_API_KEY_EXPIRY);\nconst now = new Date();\nconst daysUntilExpiry = (keyExpiry - now) / (1000 * 60 * 60 * 24);\n\nif (daysUntilExpiry < 7) {\n  // Send rotation alert\n  await $execute('mcp-crypto-trading', 'alert_manager', {\n    action: 'create',\n    alert_type: 'security',\n    symbol: 'SYSTEM',\n    condition: `API keys expire in ${Math.floor(daysUntilExpiry)} days`,\n    phone_number: '+97150XXXXXXX'\n  });\n}\n\nreturn [{ json: { days_until_expiry: daysUntilExpiry } }];"
    }
  }
  ```
</security>

### Input Validation

<security name="input_validation">
  ```json
  {
    "name": "Secure Input Validator",
    "type": "n8n-nodes-base.function",
    "parameters": {
      "functionCode": "const input = $json;\n\n// Symbol validation\nif (!input.symbol || !/^[A-Z]{2,10}USDT$/.test(input.symbol)) {\n  throw new Error('Invalid symbol format');\n}\n\n// Timeframe validation\nconst validTimeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d'];\nif (input.timeframe && !validTimeframes.includes(input.timeframe)) {\n  throw new Error('Invalid timeframe');\n}\n\n// Portfolio value validation\nif (input.portfolio_value && (input.portfolio_value < 100 || input.portfolio_value > 10000000)) {\n  throw new Error('Portfolio value out of range');\n}\n\n// Risk percentage validation  \nif (input.risk_percentage && (input.risk_percentage < 0.1 || input.risk_percentage > 10)) {\n  throw new Error('Risk percentage out of safe range');\n}\n\nreturn [{ json: input }];"
    }
  }
  ```
</security>

## Troubleshooting Guide

### Common Issues and Solutions

<troubleshooting name="connection_issues">
  <issue type="MCP Server Connection Failed">
    <symptoms>
      - "Server not found" errors
      - Tool execution timeouts
      - Connection refused messages
    </symptoms>
    <solutions>
      - Verify MCP server is running: `systemctl status mcp-crypto-trading`
      - Check server logs: `tail -f /opt/mcp-crypto-trading/logs/mcp_crypto.log`
      - Validate environment variables in n8n
      - Test server connection: `python mcp_crypto_server.py --validate`
    </solutions>
  </issue>
  
  <issue type="API Rate Limiting">
    <symptoms>
      - 429 HTTP status codes
      - "Rate limit exceeded" messages
      - Delayed responses
    </symptoms>
    <solutions>
      - Implement exponential backoff in workflows
      - Reduce scanning frequency
      - Use caching for repeated requests
      - Upgrade to premium API plans
    </solutions>
  </issue>
  
  <issue type="Tool Parameter Errors">
    <symptoms>
      - "Invalid parameter" errors
      - Tool execution failures
      - Missing required fields
    </symptoms>
    <solutions>
      - Validate input parameters before MCP calls
      - Use default values for optional parameters
      - Check parameter types and formats
      - Refer to API_REFERENCE.md for correct schemas
    </solutions>
  </issue>
</troubleshooting>

### Debugging Workflow

<troubleshooting name="debugging_steps">
  1. **Enable Debug Mode**: Set workflow to debug mode for detailed logging
  2. **Test Individual Nodes**: Execute nodes separately to isolate issues
  3. **Check MCP Server Health**: Use health check endpoint
  4. **Validate JSON Responses**: Ensure proper JSON parsing
  5. **Monitor Resource Usage**: Check CPU/memory consumption
  6. **Review Error Logs**: Examine n8n and MCP server logs
</troubleshooting>

## Production Deployment Tips

### Workflow Management

<production name="workflow_best_practices">
  <practice name="Environment Separation">
    - Use separate n8n instances for development/production
    - Environment-specific credentials and configurations
    - Staged deployment process
  </practice>
  
  <practice name="Resource Management">
    - Set appropriate execution timeouts
    - Limit concurrent executions
    - Monitor workflow performance metrics
    - Implement proper error handling and retries
  </practice>
  
  <practice name="Security">
    - Use encrypted credential storage
    - Regular security audits
    - API key rotation procedures
    - Network security and firewalls
  </practice>
</production>

### Backup and Recovery

<production name="backup_strategy">
  ```bash
  # Backup n8n workflows
  n8n export:workflow --backup --output=workflows_backup.json
  
  # Backup MCP server configurations
  tar -czf mcp_backup_$(date +%Y%m%d).tar.gz /opt/mcp-crypto-trading
  
  # Schedule regular backups
  echo "0 2 * * * /opt/scripts/backup_n8n_workflows.sh" | crontab -
  ```
</production>

---

**Professional Trading Automation Platform**  
*Complete n8n integration for institutional-grade cryptocurrency trading*

*Last Updated: December 2024 | Version: 1.0.0*

For workflow support and custom integrations: workflows@kaayaan.ai