"""
PostgreSQL client for Kaayaan infrastructure integration
Handles audit trails, performance analytics, and structured data storage
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import asyncpg
import os
import json

logger = logging.getLogger(__name__)

class PostgresClient:
    """PostgreSQL client for audit trails and performance analytics"""
    
    def __init__(self):
        # Kaayaan infrastructure connection
        self.connection_string = os.getenv(
            "POSTGRESQL_URL",
            "postgresql://user:password@postgresql:5432/database"
        )
        
        self.pool: Optional[asyncpg.Pool] = None
        
    async def connect(self):
        """Establish PostgreSQL connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=5,
                max_size=20,
                command_timeout=10,
                server_settings={
                    'jit': 'off'  # Disable JIT for better connection speed
                }
            )
            
            # Test connection and create tables if needed
            async with self.pool.acquire() as conn:
                await conn.execute('SELECT 1')
            
            await self._create_tables()
            
            logger.info("PostgreSQL connection pool established")
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Close PostgreSQL connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")
    
    async def _create_tables(self):
        """Create necessary tables with proper indexing"""
        try:
            async with self.pool.acquire() as conn:
                # Trading decisions audit table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS trading_decisions (
                        id SERIAL PRIMARY KEY,
                        decision_id VARCHAR(255) UNIQUE NOT NULL,
                        symbol VARCHAR(20) NOT NULL,
                        action VARCHAR(10) NOT NULL,
                        confidence DECIMAL(5,2),
                        reasoning TEXT,
                        market_conditions JSONB,
                        price_at_decision DECIMAL(20,8),
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        outcome VARCHAR(20),
                        outcome_price DECIMAL(20,8),
                        outcome_timestamp TIMESTAMP WITH TIME ZONE,
                        pnl_percentage DECIMAL(10,4),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                # Performance analytics table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS performance_analytics (
                        id SERIAL PRIMARY KEY,
                        metric_name VARCHAR(100) NOT NULL,
                        metric_value DECIMAL(15,6),
                        symbol VARCHAR(20),
                        timeframe VARCHAR(10),
                        metadata JSONB,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                # Risk assessments table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS risk_assessments_log (
                        id SERIAL PRIMARY KEY,
                        assessment_id VARCHAR(255) UNIQUE NOT NULL,
                        symbol VARCHAR(20) NOT NULL,
                        portfolio_value DECIMAL(15,2),
                        risk_percentage DECIMAL(5,2),
                        position_size DECIMAL(15,8),
                        stop_loss DECIMAL(20,8),
                        take_profit DECIMAL(20,8),
                        risk_reward_ratio DECIMAL(8,4),
                        max_loss_amount DECIMAL(15,2),
                        volatility_score DECIMAL(5,2),
                        market_regime VARCHAR(20),
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                # Backtest results table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS backtest_results (
                        id SERIAL PRIMARY KEY,
                        backtest_id VARCHAR(255) UNIQUE NOT NULL,
                        strategy_name VARCHAR(100) NOT NULL,
                        symbol VARCHAR(20) NOT NULL,
                        start_date DATE,
                        end_date DATE,
                        initial_capital DECIMAL(15,2),
                        final_capital DECIMAL(15,2),
                        total_return_percentage DECIMAL(10,4),
                        max_drawdown_percentage DECIMAL(10,4),
                        sharpe_ratio DECIMAL(8,4),
                        total_trades INTEGER,
                        winning_trades INTEGER,
                        losing_trades INTEGER,
                        win_rate DECIMAL(5,2),
                        avg_win_percentage DECIMAL(10,4),
                        avg_loss_percentage DECIMAL(10,4),
                        profit_factor DECIMAL(8,4),
                        strategy_parameters JSONB,
                        detailed_trades JSONB,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                # Alert history table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS alert_history (
                        id SERIAL PRIMARY KEY,
                        alert_id VARCHAR(255) NOT NULL,
                        alert_type VARCHAR(50) NOT NULL,
                        symbol VARCHAR(20),
                        conditions JSONB,
                        triggered_at TIMESTAMP WITH TIME ZONE,
                        message TEXT,
                        delivery_method VARCHAR(20),
                        delivery_status VARCHAR(20),
                        response_time_ms INTEGER,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                # System performance logs
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS system_performance (
                        id SERIAL PRIMARY KEY,
                        component VARCHAR(50) NOT NULL,
                        operation VARCHAR(100) NOT NULL,
                        execution_time_ms INTEGER,
                        success BOOLEAN,
                        error_message TEXT,
                        resource_usage JSONB,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                # Market regime history
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS market_regime_history (
                        id SERIAL PRIMARY KEY,
                        regime_id VARCHAR(255) UNIQUE NOT NULL,
                        regime VARCHAR(20) NOT NULL,
                        confidence DECIMAL(5,2),
                        indicators JSONB,
                        transition_from VARCHAR(20),
                        duration_hours INTEGER,
                        market_impact JSONB,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                # Create indexes for performance
                await self._create_indexes(conn)
                
                logger.info("PostgreSQL tables created successfully")
                
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    async def _create_indexes(self, conn):
        """Create performance indexes"""
        indexes = [
            # Trading decisions indexes
            "CREATE INDEX IF NOT EXISTS idx_trading_decisions_symbol_timestamp ON trading_decisions(symbol, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_trading_decisions_action_confidence ON trading_decisions(action, confidence DESC)",
            "CREATE INDEX IF NOT EXISTS idx_trading_decisions_outcome ON trading_decisions(outcome, pnl_percentage)",
            
            # Performance analytics indexes
            "CREATE INDEX IF NOT EXISTS idx_performance_analytics_metric_timestamp ON performance_analytics(metric_name, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_performance_analytics_symbol ON performance_analytics(symbol, timestamp DESC)",
            
            # Risk assessments indexes
            "CREATE INDEX IF NOT EXISTS idx_risk_assessments_symbol_timestamp ON risk_assessments_log(symbol, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_risk_assessments_risk_percentage ON risk_assessments_log(risk_percentage, volatility_score)",
            
            # Backtest results indexes
            "CREATE INDEX IF NOT EXISTS idx_backtest_results_strategy_symbol ON backtest_results(strategy_name, symbol)",
            "CREATE INDEX IF NOT EXISTS idx_backtest_results_performance ON backtest_results(total_return_percentage DESC, sharpe_ratio DESC)",
            
            # Alert history indexes
            "CREATE INDEX IF NOT EXISTS idx_alert_history_type_timestamp ON alert_history(alert_type, triggered_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_alert_history_symbol ON alert_history(symbol, triggered_at DESC)",
            
            # System performance indexes
            "CREATE INDEX IF NOT EXISTS idx_system_performance_component ON system_performance(component, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_system_performance_success ON system_performance(success, timestamp DESC)",
            
            # Market regime indexes
            "CREATE INDEX IF NOT EXISTS idx_market_regime_regime_timestamp ON market_regime_history(regime, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_market_regime_confidence ON market_regime_history(confidence DESC, timestamp DESC)"
        ]
        
        for index_sql in indexes:
            try:
                await conn.execute(index_sql)
            except Exception as e:
                logger.warning(f"Failed to create index: {e}")
    
    # Trading Decision Logging
    async def log_trading_decision(self, decision_data: Dict[str, Any]) -> bool:
        """Log trading decision for audit trail"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO trading_decisions (
                        decision_id, symbol, action, confidence, reasoning,
                        market_conditions, price_at_decision, timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (decision_id) DO UPDATE SET
                        outcome = EXCLUDED.outcome,
                        outcome_price = EXCLUDED.outcome_price,
                        outcome_timestamp = EXCLUDED.outcome_timestamp,
                        pnl_percentage = EXCLUDED.pnl_percentage
                """,
                    decision_data.get("decision_id"),
                    decision_data.get("symbol"),
                    decision_data.get("action"),
                    decision_data.get("confidence"),
                    decision_data.get("reasoning"),
                    json.dumps(decision_data.get("market_conditions", {})),
                    decision_data.get("price_at_decision"),
                    datetime.fromisoformat(decision_data.get("timestamp", datetime.now(timezone.utc).isoformat()))
                )
                
                logger.debug(f"Trading decision logged: {decision_data.get('decision_id')}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to log trading decision: {e}")
            return False
    
    async def update_decision_outcome(self, decision_id: str, outcome_data: Dict[str, Any]) -> bool:
        """Update trading decision with actual outcome"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    UPDATE trading_decisions SET
                        outcome = $2,
                        outcome_price = $3,
                        outcome_timestamp = $4,
                        pnl_percentage = $5
                    WHERE decision_id = $1
                """,
                    decision_id,
                    outcome_data.get("outcome"),
                    outcome_data.get("outcome_price"),
                    datetime.fromisoformat(outcome_data.get("outcome_timestamp", datetime.now(timezone.utc).isoformat())),
                    outcome_data.get("pnl_percentage")
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to update decision outcome: {e}")
            return False
    
    # Performance Analytics
    async def log_performance_metric(self, metric_data: Dict[str, Any]) -> bool:
        """Log performance metrics for analytics"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO performance_analytics (
                        metric_name, metric_value, symbol, timeframe, metadata, timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    metric_data.get("metric_name"),
                    metric_data.get("metric_value"),
                    metric_data.get("symbol"),
                    metric_data.get("timeframe"),
                    json.dumps(metric_data.get("metadata", {})),
                    datetime.fromisoformat(metric_data.get("timestamp", datetime.now(timezone.utc).isoformat()))
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to log performance metric: {e}")
            return False
    
    async def get_performance_analytics(self, metric_name: str, symbol: Optional[str] = None, 
                                      days_back: int = 30) -> List[Dict[str, Any]]:
        """Retrieve performance analytics with aggregation"""
        try:
            async with self.pool.acquire() as conn:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
                
                query = """
                    SELECT 
                        metric_name,
                        metric_value,
                        symbol,
                        timeframe,
                        metadata,
                        timestamp,
                        AVG(metric_value) OVER (
                            PARTITION BY metric_name, symbol 
                            ORDER BY timestamp 
                            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                        ) as moving_avg,
                        ROW_NUMBER() OVER (
                            PARTITION BY metric_name, symbol 
                            ORDER BY timestamp DESC
                        ) as recency_rank
                    FROM performance_analytics 
                    WHERE metric_name = $1 
                    AND timestamp >= $2
                """
                
                params = [metric_name, cutoff_date]
                
                if symbol:
                    query += " AND symbol = $3"
                    params.append(symbol)
                
                query += " ORDER BY timestamp DESC LIMIT 1000"
                
                rows = await conn.fetch(query, *params)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get performance analytics: {e}")
            return []
    
    # Risk Assessment Logging
    async def log_risk_assessment(self, risk_data: Dict[str, Any]) -> bool:
        """Log risk assessment for compliance and analysis"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO risk_assessments_log (
                        assessment_id, symbol, portfolio_value, risk_percentage,
                        position_size, stop_loss, take_profit, risk_reward_ratio,
                        max_loss_amount, volatility_score, market_regime, timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ON CONFLICT (assessment_id) DO NOTHING
                """,
                    risk_data.get("assessment_id"),
                    risk_data.get("symbol"),
                    risk_data.get("portfolio_value"),
                    risk_data.get("risk_percentage"),
                    risk_data.get("position_size"),
                    risk_data.get("stop_loss"),
                    risk_data.get("take_profit"),
                    risk_data.get("risk_reward_ratio"),
                    risk_data.get("max_loss_amount"),
                    risk_data.get("volatility_score"),
                    risk_data.get("market_regime"),
                    datetime.fromisoformat(risk_data.get("timestamp", datetime.now(timezone.utc).isoformat()))
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to log risk assessment: {e}")
            return False
    
    # Backtest Results Storage
    async def store_backtest_result(self, backtest_data: Dict[str, Any]) -> bool:
        """Store comprehensive backtest results"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO backtest_results (
                        backtest_id, strategy_name, symbol, start_date, end_date,
                        initial_capital, final_capital, total_return_percentage,
                        max_drawdown_percentage, sharpe_ratio, total_trades,
                        winning_trades, losing_trades, win_rate, avg_win_percentage,
                        avg_loss_percentage, profit_factor, strategy_parameters,
                        detailed_trades, timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
                    ON CONFLICT (backtest_id) DO NOTHING
                """,
                    backtest_data.get("backtest_id"),
                    backtest_data.get("strategy_name"),
                    backtest_data.get("symbol"),
                    datetime.fromisoformat(backtest_data.get("start_date")).date(),
                    datetime.fromisoformat(backtest_data.get("end_date")).date(),
                    backtest_data.get("initial_capital"),
                    backtest_data.get("final_capital"),
                    backtest_data.get("total_return_percentage"),
                    backtest_data.get("max_drawdown_percentage"),
                    backtest_data.get("sharpe_ratio"),
                    backtest_data.get("total_trades"),
                    backtest_data.get("winning_trades"),
                    backtest_data.get("losing_trades"),
                    backtest_data.get("win_rate"),
                    backtest_data.get("avg_win_percentage"),
                    backtest_data.get("avg_loss_percentage"),
                    backtest_data.get("profit_factor"),
                    json.dumps(backtest_data.get("strategy_parameters", {})),
                    json.dumps(backtest_data.get("detailed_trades", [])),
                    datetime.fromisoformat(backtest_data.get("timestamp", datetime.now(timezone.utc).isoformat()))
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to store backtest result: {e}")
            return False
    
    async def get_best_strategies(self, symbol: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get best performing strategies based on multiple metrics"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT 
                        strategy_name,
                        symbol,
                        COUNT(*) as backtest_count,
                        AVG(total_return_percentage) as avg_return,
                        AVG(sharpe_ratio) as avg_sharpe,
                        AVG(max_drawdown_percentage) as avg_drawdown,
                        AVG(win_rate) as avg_win_rate,
                        MAX(total_return_percentage) as best_return,
                        STDDEV(total_return_percentage) as return_consistency,
                        (AVG(total_return_percentage) / NULLIF(AVG(max_drawdown_percentage), 0)) as risk_adj_return
                    FROM backtest_results
                    WHERE total_trades >= 10
                """
                
                params = []
                if symbol:
                    query += " AND symbol = $1"
                    params.append(symbol)
                
                query += """
                    GROUP BY strategy_name, symbol
                    HAVING COUNT(*) >= 3
                    ORDER BY avg_sharpe DESC, avg_return DESC
                    LIMIT ${}
                """.format(len(params) + 1)
                
                params.append(limit)
                
                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get best strategies: {e}")
            return []
    
    # Alert History
    async def log_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Log alert delivery and response times"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO alert_history (
                        alert_id, alert_type, symbol, conditions, triggered_at,
                        message, delivery_method, delivery_status, response_time_ms
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                    alert_data.get("alert_id"),
                    alert_data.get("alert_type"),
                    alert_data.get("symbol"),
                    json.dumps(alert_data.get("conditions", {})),
                    datetime.fromisoformat(alert_data.get("triggered_at", datetime.now(timezone.utc).isoformat())),
                    alert_data.get("message"),
                    alert_data.get("delivery_method"),
                    alert_data.get("delivery_status"),
                    alert_data.get("response_time_ms")
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to log alert: {e}")
            return False
    
    # System Performance Monitoring
    async def log_system_performance(self, performance_data: Dict[str, Any]) -> bool:
        """Log system performance for monitoring"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO system_performance (
                        component, operation, execution_time_ms, success,
                        error_message, resource_usage, timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                    performance_data.get("component"),
                    performance_data.get("operation"),
                    performance_data.get("execution_time_ms"),
                    performance_data.get("success"),
                    performance_data.get("error_message"),
                    json.dumps(performance_data.get("resource_usage", {})),
                    datetime.fromisoformat(performance_data.get("timestamp", datetime.now(timezone.utc).isoformat()))
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to log system performance: {e}")
            return False
    
    async def get_system_health_metrics(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get system health metrics and statistics"""
        try:
            async with self.pool.acquire() as conn:
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
                
                # Get overall system health
                health_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_operations,
                        COUNT(*) FILTER (WHERE success = true) as successful_operations,
                        AVG(execution_time_ms) as avg_execution_time,
                        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time_ms) as p95_execution_time,
                        COUNT(DISTINCT component) as active_components
                    FROM system_performance 
                    WHERE timestamp >= $1
                """, cutoff_time)
                
                # Get component-wise performance
                component_stats = await conn.fetch("""
                    SELECT 
                        component,
                        COUNT(*) as operations,
                        COUNT(*) FILTER (WHERE success = true) as successful,
                        AVG(execution_time_ms) as avg_time,
                        MAX(execution_time_ms) as max_time
                    FROM system_performance 
                    WHERE timestamp >= $1
                    GROUP BY component
                    ORDER BY operations DESC
                """, cutoff_time)
                
                return {
                    "health_stats": dict(health_stats) if health_stats else {},
                    "component_stats": [dict(row) for row in component_stats]
                }
                
        except Exception as e:
            logger.error(f"Failed to get system health metrics: {e}")
            return {"health_stats": {}, "component_stats": []}
    
    # Market Regime Tracking
    async def log_market_regime(self, regime_data: Dict[str, Any]) -> bool:
        """Log market regime transitions"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO market_regime_history (
                        regime_id, regime, confidence, indicators, transition_from,
                        duration_hours, market_impact, timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (regime_id) DO NOTHING
                """,
                    regime_data.get("regime_id"),
                    regime_data.get("regime"),
                    regime_data.get("confidence"),
                    json.dumps(regime_data.get("indicators", {})),
                    regime_data.get("transition_from"),
                    regime_data.get("duration_hours"),
                    json.dumps(regime_data.get("market_impact", {})),
                    datetime.fromisoformat(regime_data.get("timestamp", datetime.now(timezone.utc).isoformat()))
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to log market regime: {e}")
            return False
    
    async def get_decision_performance_summary(self, symbol: Optional[str] = None, days_back: int = 30) -> Dict[str, Any]:
        """Get comprehensive decision performance summary"""
        try:
            async with self.pool.acquire() as conn:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
                
                query = """
                    SELECT 
                        COUNT(*) as total_decisions,
                        COUNT(*) FILTER (WHERE outcome = 'positive') as positive_outcomes,
                        COUNT(*) FILTER (WHERE outcome = 'negative') as negative_outcomes,
                        AVG(confidence) as avg_confidence,
                        AVG(pnl_percentage) FILTER (WHERE pnl_percentage IS NOT NULL) as avg_pnl,
                        STDDEV(pnl_percentage) FILTER (WHERE pnl_percentage IS NOT NULL) as pnl_volatility,
                        MAX(pnl_percentage) as best_trade,
                        MIN(pnl_percentage) as worst_trade,
                        COUNT(*) FILTER (WHERE action = 'BUY') as buy_signals,
                        COUNT(*) FILTER (WHERE action = 'SELL') as sell_signals,
                        COUNT(*) FILTER (WHERE action = 'HOLD') as hold_signals
                    FROM trading_decisions 
                    WHERE timestamp >= $1
                """
                
                params = [cutoff_date]
                if symbol:
                    query += " AND symbol = $2"
                    params.append(symbol)
                
                result = await conn.fetchrow(query, *params)
                
                return dict(result) if result else {}
                
        except Exception as e:
            logger.error(f"Failed to get decision performance summary: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform PostgreSQL health check"""
        try:
            if not self.pool:
                await self.connect()
            
            async with self.pool.acquire() as conn:
                # Test basic operations
                await conn.execute('SELECT 1')
                
                # Get database statistics
                stats = await conn.fetchrow("""
                    SELECT 
                        pg_database_size(current_database()) as db_size,
                        (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                        (SELECT count(*) FROM trading_decisions) as total_decisions,
                        (SELECT count(*) FROM performance_analytics) as total_metrics
                """)
                
                return {
                    "status": "healthy",
                    "database_size": stats["db_size"] if stats else 0,
                    "active_connections": stats["active_connections"] if stats else 0,
                    "total_decisions": stats["total_decisions"] if stats else 0,
                    "total_metrics": stats["total_metrics"] if stats else 0,
                    "pool_size": self.pool.get_size(),
                    "pool_available": self.pool.get_idle_size()
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }