# MCP Crypto Trading Analysis - System Architecture

<metadata>
purpose: Technical system architecture documentation for MCP Crypto Trading platform
type: architecture
language: Python
dependencies: MCP, MongoDB, Redis, PostgreSQL, Docker, nginx
last-updated: 2024-12-19
</metadata>

<overview>
The MCP Crypto Trading Analysis platform is built as a microservices-based system with enterprise-grade architecture. It provides real-time cryptocurrency analysis through 7 intelligent MCP tools, integrated with Kaayaan infrastructure for production deployment.
</overview>

## System Architecture Overview

```mermaid
graph TB
    subgraph "Client Layer"
        A[n8n Workflows]
        B[REST API Clients]
        C[Direct MCP Clients]
    end
    
    subgraph "Load Balancer"
        D[Nginx Load Balancer]
        E[SSL Termination]
        F[Rate Limiting]
    end
    
    subgraph "Application Layer"
        G[MCP Crypto Server]
        H[Analysis Engine]
        I[Infrastructure Factory]
    end
    
    subgraph "Core Services"
        J[Market Scanner]
        K[Portfolio Tracker] 
        L[Risk Manager]
        M[Alert Manager]
        N[Backtester]
    end
    
    subgraph "Data Layer"
        O[(MongoDB)]
        P[(Redis Cache)]
        Q[(PostgreSQL)]
    end
    
    subgraph "External APIs"
        R[Binance API]
        S[CoinGecko API]
        T[CoinMarketCap API]
        U[WhatsApp API]
    end
    
    A --> D
    B --> D
    C --> D
    D --> G
    G --> H
    G --> I
    H --> J
    H --> K
    H --> L
    H --> M
    H --> N
    J --> O
    J --> P
    K --> O
    L --> O
    M --> Q
    M --> U
    N --> O
    I --> O
    I --> P
    I --> Q
    G --> R
    G --> S
    G --> T
```

## Core Components

### MCP Server Layer
<component name="mcp_crypto_server">
  <purpose>Main MCP protocol server handling tool execution and client communication</purpose>
  <responsibilities>
    - MCP protocol implementation (stdio/HTTP)
    - Tool registration and execution routing
    - Request validation and error handling
    - Response formatting and serialization
    - Client session management
  </responsibilities>
  <interfaces>
    <interface type="MCP Protocol" transport="stdio/HTTP">Tool execution requests</interface>
    <interface type="Internal API" transport="async">Infrastructure services communication</interface>
  </interfaces>
  <configuration>
    <setting name="port" default="8080">HTTP server port</setting>
    <setting name="workers" default="4">Async worker processes</setting>
    <setting name="timeout" default="30">Request timeout seconds</setting>
  </configuration>
</component>

### Analysis Engine
<component name="analysis_engine">
  <purpose>Core cryptocurrency analysis with institutional-grade indicators</purpose>
  <responsibilities>
    - Technical indicator calculations (Order Blocks, FVG, BoS)
    - Market sentiment analysis
    - Volatility assessment
    - Trend identification
    - Smart recommendation generation
  </responsibilities>
  <algorithms>
    <algorithm name="Order Block Detection">
      - Identify supply/demand zones based on price action
      - Calculate strength scores using volume and rejection metrics
      - Classify as bullish/bearish with confidence levels
    </algorithm>
    <algorithm name="Fair Value Gap Analysis">
      - Detect price inefficiencies in market structure
      - Measure gap significance and fill probability
      - Generate trade entry/exit recommendations
    </algorithm>
    <algorithm name="Intelligent Scoring">
      - Combine multiple technical factors
      - Weight based on market conditions
      - Generate 0-10 confidence scores
    </algorithm>
  </algorithms>
</component>

### Infrastructure Factory
<component name="kaayaan_factory">
  <purpose>Manages all infrastructure connections and service instantiation</purpose>
  <responsibilities>
    - Database connection management
    - Service dependency injection
    - Health monitoring
    - Resource cleanup
    - Connection pooling
  </responsibilities>
  <connections>
    <connection type="MongoDB" uri="mongodb://username:password@mongodb:27017/">
      - Analysis data storage
      - Portfolio tracking
      - Historical records
    </connection>
    <connection type="Redis" uri="redis://:password@redis:6379">
      - Result caching
      - Session management
      - Rate limiting
    </connection>
    <connection type="PostgreSQL" uri="postgresql://user:password@postgresql:5432/database">
      - n8n workflow data
      - User management
      - Alert configurations
    </connection>
  </connections>
</component>

## Data Flow Architecture

### Request Processing Flow
```mermaid
sequenceDiagram
    participant C as Client
    participant N as Nginx
    participant M as MCP Server
    participant A as Analysis Engine
    participant D as Database
    participant E as External APIs
    
    C->>N: MCP Tool Request
    N->>M: Forward Request (rate limited)
    M->>M: Validate Parameters
    M->>A: Execute Analysis
    A->>E: Fetch Market Data
    E-->>A: Market Data Response
    A->>D: Cache Results
    A->>A: Generate Analysis
    A-->>M: Analysis Results
    M->>M: Format MCP Response
    M-->>N: Tool Response
    N-->>C: Final Response
```

### Data Pipeline Architecture
<pipeline name="market_data_pipeline">
  <stage name="ingestion">
    - Parallel API calls to Binance, CoinGecko, CoinMarketCap
    - Rate limiting and retry logic
    - Data validation and normalization
  </stage>
  <stage name="processing">
    - Technical indicator calculations
    - Signal generation
    - Confidence scoring
  </stage>
  <stage name="storage">
    - MongoDB for analysis results
    - Redis for hot cache data
    - PostgreSQL for user/workflow data
  </stage>
  <stage name="notification">
    - Alert trigger evaluation
    - WhatsApp message dispatch
    - Portfolio update notifications
  </stage>
</pipeline>

## Database Schema Design

### MongoDB Collections
<database name="mongodb">
  <collection name="analyses">
    <schema>
      {
        "_id": ObjectId,
        "symbol": "BTCUSDT",
        "timestamp": ISODate,
        "timeframe": "1h",
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
            "timestamp": ISODate
          }
        ],
        "recommendation": {
          "action": "BUY",
          "confidence": 87.3,
          "reasoning": "Strong bullish trend..."
        },
        "created_at": ISODate,
        "ttl": ISODate
      }
    </schema>
    <indexes>
      - symbol_1_timestamp_-1 (compound)
      - created_at_1 (TTL index, 7 days)
      - analysis.confidence_-1 (performance)
    </indexes>
  </collection>
  
  <collection name="portfolios">
    <schema>
      {
        "_id": ObjectId,
        "portfolio_id": "trading_portfolio_001",
        "user_id": "user_123",
        "positions": [
          {
            "symbol": "BTCUSDT",
            "size": 1.5,
            "entry_price": 42000,
            "current_price": 43500,
            "pnl_percent": 3.57
          }
        ],
        "risk_metrics": {
          "portfolio_var_95": 2150.30,
          "max_drawdown": 8.2,
          "sharpe_ratio": 1.45
        },
        "last_updated": ISODate
      }
    </schema>
  </collection>
  
  <collection name="alerts">
    <schema>
      {
        "_id": ObjectId,
        "alert_id": "alert_001_btc_price",
        "user_id": "user_123",
        "symbol": "BTCUSDT",
        "type": "price",
        "condition": "price > 45000",
        "status": "active",
        "whatsapp_number": "+97150XXXXXXX",
        "created_at": ISODate,
        "triggered_at": ISODate
      }
    </schema>
  </collection>
</database>

### Redis Cache Structure
<database name="redis">
  <keyspace db="0" purpose="Result Caching">
    - analysis:{symbol}:{timeframe} (TTL: 300s)
    - market_scan:{scan_type}:{timestamp} (TTL: 60s)
    - portfolio:{portfolio_id} (TTL: 30s)
  </keyspace>
  
  <keyspace db="1" purpose="Session Management">
    - session:{client_id} (TTL: 3600s)
    - rate_limit:{ip_address} (TTL: 60s)
  </keyspace>
  
  <keyspace db="2" purpose="Task Queues">
    - alerts:pending (List)
    - backtest:queue (List)
    - notifications:queue (List)
  </keyspace>
</database>

### PostgreSQL Schema (n8n Integration)
<database name="postgresql">
  <table name="workflow_executions">
    - execution_id (Primary Key)
    - workflow_id
    - execution_data (JSONB)
    - status
    - created_at, updated_at
  </table>
  
  <table name="mcp_tool_logs">
    - log_id (Primary Key)
    - tool_name
    - arguments (JSONB)
    - response (JSONB)
    - execution_time_ms
    - status
    - error_message
    - created_at
  </table>
</database>

## Security Architecture

### Authentication & Authorization
<security_layer name="authentication">
  <mechanism name="API Keys">
    - External API authentication (Binance, CoinGecko, etc.)
    - Stored in secure environment variables
    - Rotation every 90 days
  </mechanism>
  
  <mechanism name="MCP Protocol Security">
    - Client authentication via stdio/HTTP
    - Request signing for sensitive operations
    - IP whitelisting for production
  </mechanism>
  
  <mechanism name="Database Security">
    - Connection encryption (TLS 1.3)
    - Username/password authentication
    - Role-based access control
  </mechanism>
</security_layer>

### Data Protection
<security_layer name="data_protection">
  <encryption at_rest="true">
    - MongoDB encryption at rest
    - SSL certificate storage
    - Backup encryption
  </encryption>
  
  <encryption in_transit="true">
    - HTTPS/TLS 1.3 for all external communication
    - Database connections over SSL
    - WhatsApp API secure messaging
  </encryption>
  
  <privacy_controls>
    - No sensitive data in logs
    - User position data anonymization
    - GDPR compliance measures
  </privacy_controls>
</security_layer>

## Performance Architecture

### Caching Strategy
<performance_layer name="caching">
  <cache_tier name="L1_Application">
    - In-memory Python dictionaries
    - LRU eviction policy
    - 50MB memory limit
  </cache_tier>
  
  <cache_tier name="L2_Redis">
    - Analysis results (5 min TTL)
    - Market data (1 min TTL)
    - Portfolio snapshots (30 sec TTL)
  </cache_tier>
  
  <cache_tier name="L3_Database">
    - MongoDB result storage
    - Historical data archive
    - Long-term backtesting data
  </cache_tier>
</performance_layer>

### Load Balancing & Scaling
<performance_layer name="scaling">
  <horizontal_scaling>
    - Multiple MCP server instances
    - Nginx upstream load balancing
    - Session affinity for stateful operations
  </horizontal_scaling>
  
  <vertical_scaling>
    - CPU: 4+ cores recommended
    - RAM: 8GB minimum, 16GB production
    - Storage: SSD for database performance
  </vertical_scaling>
  
  <auto_scaling>
    - Docker Swarm service scaling
    - CPU/Memory threshold-based scaling
    - Queue depth monitoring for backtest services
  </auto_scaling>
</performance_layer>

### Performance Benchmarks
<performance_metrics>
  <metric name="analyze_crypto" target="<500ms" p95="300ms">
    Single symbol analysis with full indicators
  </metric>
  
  <metric name="market_scanner" target="<3s" p95="2.1s">
    Full market scan of 200+ symbols
  </metric>
  
  <metric name="portfolio_monitor" target="<200ms" p95="150ms">
    Portfolio health check for 10 positions
  </metric>
  
  <metric name="risk_assessment" target="<100ms" p95="75ms">
    Position sizing calculation
  </metric>
  
  <metric name="historical_backtest" target="<30s" p95="18s">
    1-year backtest with 1h timeframe
  </metric>
</performance_metrics>

## Monitoring & Observability

### Health Monitoring
<monitoring_layer name="health_checks">
  <endpoint path="/health" purpose="Basic health check">
    - Service status
    - Database connectivity
    - External API availability
  </endpoint>
  
  <endpoint path="/health/infrastructure" purpose="Detailed infrastructure health">
    - Connection pool status
    - Cache hit rates
    - Performance metrics
  </endpoint>
  
  <endpoint path="/metrics" purpose="Prometheus metrics">
    - Request counts and latency
    - Error rates by tool
    - Resource utilization
  </endpoint>
</monitoring_layer>

### Logging Architecture
<monitoring_layer name="logging">
  <log_level name="INFO" default="true">
    - Tool execution summaries
    - Performance benchmarks
    - Health check results
  </log_level>
  
  <log_level name="ERROR" alerts="true">
    - API failures and retries
    - Database connection issues
    - Tool execution failures
  </log_level>
  
  <log_rotation>
    - Daily rotation
    - 30-day retention
    - Compressed archive storage
  </log_rotation>
</monitoring_layer>

### Alerting System
<monitoring_layer name="alerting">
  <alert_channel name="WhatsApp" priority="high">
    - System failures
    - Performance degradation
    - Security incidents
  </alert_channel>
  
  <alert_thresholds>
    - CPU usage > 80%
    - Memory usage > 85%
    - Error rate > 5%
    - Response time > 1000ms
  </alert_thresholds>
</monitoring_layer>

## Deployment Architecture

### Container Architecture
<deployment name="containerization">
  <container name="mcp-crypto-server">
    <base_image>python:3.12-slim</base_image>
    <resources>
      <limits cpu="2" memory="4Gi"/>
      <requests cpu="1" memory="2Gi"/>
    </resources>
    <health_check>
      <test>curl -f http://localhost:8080/health</test>
      <interval>30s</interval>
      <timeout>10s</timeout>
      <retries>3</retries>
    </health_check>
  </container>
  
  <container name="nginx-lb">
    <base_image>nginx:alpine</base_image>
    <config_files>
      - /etc/nginx/nginx.conf
      - /etc/nginx/ssl/
    </config_files>
  </container>
</deployment>

### Network Architecture
<deployment name="networking">
  <network name="kaayaan" type="bridge">
    - MCP server containers
    - Database services
    - Nginx load balancer
  </network>
  
  <ports>
    - 80/tcp: HTTP (redirect to HTTPS)
    - 443/tcp: HTTPS/TLS
    - 8080/tcp: Internal MCP server
  </ports>
  
  <security_groups>
    - Inbound: 80, 443 from 0.0.0.0/0
    - Inbound: 8080 from nginx containers only
    - Outbound: 443 to external APIs
  </security_groups>
</deployment>

### Infrastructure as Code
<deployment name="infrastructure_code">
  <docker_compose>
    - docker-compose.production.yml
    - Environment-specific overrides
    - Service dependency management
  </docker_compose>
  
  <configuration_management>
    - .env.production configuration
    - SSL certificate management
    - Database initialization scripts
  </configuration_management>
  
  <automation>
    - Health check validation
    - Backup automation
    - Log rotation scripts
    - Performance monitoring
  </automation>
</deployment>

## Disaster Recovery

### Backup Strategy
<disaster_recovery name="backup">
  <database_backup frequency="daily">
    - MongoDB full backup (mongodump)
    - Redis AOF persistence
    - PostgreSQL continuous archiving
  </database_backup>
  
  <application_backup frequency="daily">
    - Configuration files
    - SSL certificates
    - Application logs
    - Custom scripts
  </application_backup>
  
  <retention_policy>
    - Daily backups: 14 days
    - Weekly backups: 12 weeks
    - Monthly backups: 12 months
  </retention_policy>
</disaster_recovery>

### Recovery Procedures
<disaster_recovery name="recovery">
  <rto target="15_minutes">Recovery Time Objective</rto>
  <rpo target="5_minutes">Recovery Point Objective</rpo>
  
  <recovery_steps>
    1. Stop affected services
    2. Restore database from backup
    3. Restore application configuration
    4. Restart services in dependency order
    5. Verify system health
    6. Resume normal operations
  </recovery_steps>
  
  <testing_schedule frequency="monthly">
    - Disaster recovery drills
    - Backup integrity verification
    - Recovery procedure validation
  </testing_schedule>
</disaster_recovery>

---

**Enterprise-Grade Trading Intelligence Architecture**  
*Designed for high availability, scalability, and institutional-grade reliability*

*Last Updated: December 2024 | Version: 1.0.0*