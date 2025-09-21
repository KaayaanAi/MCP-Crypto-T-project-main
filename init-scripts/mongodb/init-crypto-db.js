// MongoDB Initialization Script for MCP Crypto Trading
// Creates crypto_trading database with required collections and indexes
// Security hardened - Production ready
// Last Updated: 2025-09-21

db = db.getSiblingDB('crypto_trading');

// Create collections with validation schemas
db.createCollection('market_data', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["symbol", "timestamp", "price"],
      properties: {
        symbol: { bsonType: "string" },
        timestamp: { bsonType: "date" },
        price: { bsonType: "number" },
        volume: { bsonType: "number" },
        source: { bsonType: "string" }
      }
    }
  }
});

db.createCollection('trading_signals', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["symbol", "signal_type", "timestamp"],
      properties: {
        symbol: { bsonType: "string" },
        signal_type: { bsonType: "string", enum: ["BUY", "SELL", "HOLD"] },
        timestamp: { bsonType: "date" },
        confidence: { bsonType: "number", minimum: 0, maximum: 1 },
        indicators: { bsonType: "object" }
      }
    }
  }
});

db.createCollection('portfolio_positions', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["symbol", "quantity", "entry_price", "timestamp"],
      properties: {
        symbol: { bsonType: "string" },
        quantity: { bsonType: "number" },
        entry_price: { bsonType: "number" },
        current_price: { bsonType: "number" },
        timestamp: { bsonType: "date" },
        position_type: { bsonType: "string", enum: ["LONG", "SHORT"] },
        exit_price: { bsonType: "number" },
        exit_timestamp: { bsonType: "date" },
        pnl: { bsonType: "number" },
        status: { bsonType: "string", enum: ["OPEN", "CLOSED", "PENDING"] }
      }
    }
  }
});

// Risk management collection
db.createCollection('risk_metrics', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["timestamp", "portfolio_value"],
      properties: {
        timestamp: { bsonType: "date" },
        portfolio_value: { bsonType: "number" },
        total_exposure: { bsonType: "number" },
        var_95: { bsonType: "number" },
        sharpe_ratio: { bsonType: "number" },
        max_drawdown: { bsonType: "number" },
        created_at: { bsonType: "date" }
      }
    }
  }
});

// System audit collection for security tracking
db.createCollection('system_audit', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["event_type", "timestamp"],
      properties: {
        event_type: { bsonType: "string" },
        event_description: { bsonType: "string" },
        timestamp: { bsonType: "date" },
        user_name: { bsonType: "string" },
        ip_address: { bsonType: "string" },
        session_id: { bsonType: "string" }
      }
    }
  }
});

// Create comprehensive indexes for performance
// Market data indexes
db.market_data.createIndex({ "symbol": 1, "timestamp": -1 });
db.market_data.createIndex({ "timestamp": -1 });
db.market_data.createIndex({ "source": 1, "timestamp": -1 });

// Trading signals indexes
db.trading_signals.createIndex({ "symbol": 1, "timestamp": -1 });
db.trading_signals.createIndex({ "signal_type": 1, "timestamp": -1 });
db.trading_signals.createIndex({ "confidence": -1, "timestamp": -1 });

// Portfolio positions indexes
db.portfolio_positions.createIndex({ "symbol": 1 });
db.portfolio_positions.createIndex({ "status": 1, "timestamp": -1 });
db.portfolio_positions.createIndex({ "position_type": 1, "timestamp": -1 });

// Risk metrics indexes
db.risk_metrics.createIndex({ "timestamp": -1 });
db.risk_metrics.createIndex({ "portfolio_value": -1, "timestamp": -1 });

// System audit indexes
db.system_audit.createIndex({ "timestamp": -1 });
db.system_audit.createIndex({ "event_type": 1, "timestamp": -1 });
db.system_audit.createIndex({ "user_name": 1, "timestamp": -1 });

// Initialize with audit log
db.system_audit.insertOne({
  event_type: "DATABASE_INIT",
  event_description: "MongoDB crypto_trading database initialized successfully",
  timestamp: new Date(),
  user_name: "system",
  ip_address: "localhost",
  session_id: "init_script"
});

// Initialize risk metrics with zero values
db.risk_metrics.insertOne({
  timestamp: new Date(),
  portfolio_value: 0,
  total_exposure: 0,
  var_95: 0,
  sharpe_ratio: 0,
  max_drawdown: 0,
  created_at: new Date()
});

print("MongoDB crypto_trading database initialized successfully with security audit");