"""
Database Manager for Kaayaan Infrastructure
Handles data persistence across MongoDB, Redis, and PostgreSQL
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
import motor.motor_asyncio as motor
import redis.asyncio as redis
import asyncpg
from dataclasses import asdict

from models.kaayaan_models import *

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Centralized database management for multi-database architecture
    - MongoDB: Analysis results, trading signals, historical patterns
    - Redis: Real-time data cache, session data
    - PostgreSQL: Audit logs, user data, system metrics
    """
    
    def __init__(self, mongodb_client: motor.AsyncIOMotorClient,
                 redis_client: redis.Redis, postgres_pool: asyncpg.Pool):
        self.mongodb_client = mongodb_client
        self.redis_client = redis_client
        self.postgres_pool = postgres_pool
        
        # Database references
        self.crypto_db = mongodb_client.crypto_trading
        self.analysis_collection = self.crypto_db.analysis_results
        self.portfolio_collection = self.crypto_db.portfolios
        self.opportunities_collection = self.crypto_db.opportunities
        self.alerts_collection = self.crypto_db.alerts
        self.backtests_collection = self.crypto_db.backtests
        
        # Cache TTL settings (seconds)
        self.cache_ttl = {
            'market_context': 300,      # 5 minutes
            'analysis': 900,            # 15 minutes
            'price_data': 60,           # 1 minute
            'portfolio': 300,           # 5 minutes
            'opportunities': 600        # 10 minutes
        }
        
    async def initialize_collections(self):
        """Initialize database collections with proper indexes"""
        try:
            # MongoDB indexes for performance
            await self.analysis_collection.create_index([
                ("symbol", 1),
                ("timestamp", -1)
            ])
            
            await self.opportunities_collection.create_index([
                ("confidence_score", -1),
                ("detected_at", -1)
            ])
            
            await self.alerts_collection.create_index([
                ("symbol", 1),
                ("status", 1),
                ("phone_number", 1)
            ])
            
            await self.portfolio_collection.create_index([
                ("portfolio_id", 1),
                ("timestamp", -1)
            ])
            
            # PostgreSQL tables creation
            await self._create_postgres_tables()
            
            logger.info("Database collections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")
            raise
    
    async def _create_postgres_tables(self):
        """Create PostgreSQL tables for audit logs and metrics"""
        try:
            async with self.postgres_pool.acquire() as conn:
                # Audit logs table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id UUID PRIMARY KEY,
                        action VARCHAR(100) NOT NULL,
                        symbol VARCHAR(20),
                        user_id VARCHAR(50),
                        parameters JSONB,
                        result JSONB,
                        execution_time_ms FLOAT,
                        success BOOLEAN,
                        error_message TEXT,
                        timestamp TIMESTAMPTZ DEFAULT NOW()
                    )
                ''')
                
                # System metrics table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id SERIAL PRIMARY KEY,
                        metric_name VARCHAR(100) NOT NULL,
                        metric_value FLOAT NOT NULL,
                        tags JSONB,
                        timestamp TIMESTAMPTZ DEFAULT NOW()
                    )
                ''')
                
                # User sessions table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        session_id UUID PRIMARY KEY,
                        user_id VARCHAR(50),
                        portfolio_id VARCHAR(50),
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        last_activity TIMESTAMPTZ DEFAULT NOW(),
                        is_active BOOLEAN DEFAULT TRUE
                    )
                ''')
                
                # Create indexes
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)')
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)')
                await conn.execute('CREATE INDEX IF NOT EXISTS idx_system_metrics_name_timestamp ON system_metrics(metric_name, timestamp)')
                
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL tables: {e}")
            raise
    
    # ==================== ANALYSIS DATA ====================
    
    async def save_analysis(self, analysis: Union[EnhancedAnalysisResult, Dict[str, Any]]):
        """Save analysis result to MongoDB with Redis caching"""
        try:
            # Convert to dict if needed
            if isinstance(analysis, EnhancedAnalysisResult):
                analysis_dict = analysis.dict()
            else:
                analysis_dict = analysis
            
            # Add timestamp if not present
            if 'timestamp' not in analysis_dict:
                analysis_dict['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            # Save to MongoDB
            result = await self.analysis_collection.insert_one(analysis_dict)
            
            # Cache in Redis for quick access
            cache_key = f"analysis:{analysis_dict['symbol']}:{analysis_dict['timeframe']}"
            await self.redis_client.setex(
                cache_key, 
                self.cache_ttl['analysis'],
                json.dumps(analysis_dict, default=str)
            )
            
            logger.info(f"Analysis saved for {analysis_dict['symbol']}: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to save analysis: {e}")
            raise
    
    async def get_latest_analysis(self, symbol: str, timeframe: str = "1h") -> Optional[Dict[str, Any]]:
        """Get latest analysis from cache or database"""
        try:
            # Try Redis cache first
            cache_key = f"analysis:{symbol}:{timeframe}"
            cached = await self.redis_client.get(cache_key)
            
            if cached:
                return json.loads(cached)
            
            # Fall back to MongoDB
            result = await self.analysis_collection.find_one(
                {"symbol": symbol, "timeframe": timeframe},
                sort=[("timestamp", -1)]
            )
            
            if result:
                # Remove MongoDB ObjectId for JSON serialization
                result.pop('_id', None)
                
                # Cache the result
                await self.redis_client.setex(
                    cache_key,
                    self.cache_ttl['analysis'],
                    json.dumps(result, default=str)
                )
                
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get analysis for {symbol}: {e}")
            return None
    
    async def get_historical_analysis(self, symbol: str, 
                                    start_date: datetime, 
                                    end_date: datetime,
                                    timeframe: str = "1h") -> List[Dict[str, Any]]:
        """Get historical analysis data for backtesting and patterns"""
        try:
            cursor = self.analysis_collection.find({
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                }
            }).sort("timestamp", 1)
            
            results = []
            async for doc in cursor:
                doc.pop('_id', None)
                results.append(doc)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get historical analysis: {e}")
            return []
    
    # ==================== PORTFOLIO MANAGEMENT ====================
    
    async def save_portfolio_analysis(self, portfolio_analysis: Union[PortfolioAnalysis, Dict[str, Any]]):
        """Save portfolio analysis to MongoDB"""
        try:
            if isinstance(portfolio_analysis, PortfolioAnalysis):
                portfolio_dict = portfolio_analysis.dict()
            else:
                portfolio_dict = portfolio_analysis
            
            # Ensure timestamp
            if 'timestamp' not in portfolio_dict:
                portfolio_dict['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            result = await self.portfolio_collection.insert_one(portfolio_dict)
            
            # Cache latest portfolio state
            cache_key = f"portfolio:{portfolio_dict['portfolio_id']}"
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl['portfolio'],
                json.dumps(portfolio_dict, default=str)
            )
            
            logger.info(f"Portfolio analysis saved for {portfolio_dict['portfolio_id']}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to save portfolio analysis: {e}")
            raise
    
    async def get_latest_portfolio(self, portfolio_id: str) -> Optional[Dict[str, Any]]:
        """Get latest portfolio state"""
        try:
            # Try cache first
            cache_key = f"portfolio:{portfolio_id}"
            cached = await self.redis_client.get(cache_key)
            
            if cached:
                return json.loads(cached)
            
            # Query database
            result = await self.portfolio_collection.find_one(
                {"portfolio_id": portfolio_id},
                sort=[("timestamp", -1)]
            )
            
            if result:
                result.pop('_id', None)
                
                # Cache the result
                await self.redis_client.setex(
                    cache_key,
                    self.cache_ttl['portfolio'],
                    json.dumps(result, default=str)
                )
                
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get portfolio {portfolio_id}: {e}")
            return None
    
    # ==================== TRADING OPPORTUNITIES ====================
    
    async def save_opportunities(self, opportunities: List[TradingOpportunity]):
        """Save trading opportunities to MongoDB"""
        try:
            if not opportunities:
                return []
            
            # Convert to dicts
            opportunity_dicts = []
            for opp in opportunities:
                if isinstance(opp, TradingOpportunity):
                    opp_dict = opp.dict()
                else:
                    opp_dict = opp
                opportunity_dicts.append(opp_dict)
            
            # Bulk insert
            result = await self.opportunities_collection.insert_many(opportunity_dicts)
            
            # Cache high-confidence opportunities
            high_confidence = [opp for opp in opportunity_dicts if opp.get('confidence_score', 0) >= 80]
            if high_confidence:
                await self.redis_client.setex(
                    "opportunities:high_confidence",
                    self.cache_ttl['opportunities'],
                    json.dumps(high_confidence, default=str)
                )
            
            logger.info(f"Saved {len(opportunities)} trading opportunities")
            return [str(id) for id in result.inserted_ids]
            
        except Exception as e:
            logger.error(f"Failed to save opportunities: {e}")
            raise
    
    async def get_active_opportunities(self, min_confidence: float = 70) -> List[Dict[str, Any]]:
        """Get active trading opportunities above confidence threshold"""
        try:
            # Check cache for high-confidence opportunities first
            if min_confidence >= 80:
                cached = await self.redis_client.get("opportunities:high_confidence")
                if cached:
                    opportunities = json.loads(cached)
                    return [opp for opp in opportunities if opp.get('confidence_score', 0) >= min_confidence]
            
            # Query database
            cursor = self.opportunities_collection.find({
                "confidence_score": {"$gte": min_confidence},
                "$or": [
                    {"expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}},
                    {"expires_at": None}
                ]
            }).sort("confidence_score", -1).limit(20)
            
            opportunities = []
            async for doc in cursor:
                doc.pop('_id', None)
                opportunities.append(doc)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Failed to get active opportunities: {e}")
            return []
    
    # ==================== ALERT MANAGEMENT ====================
    
    async def save_alert(self, alert: Alert) -> str:
        """Save trading alert configuration"""
        try:
            alert_dict = alert.dict() if isinstance(alert, Alert) else alert
            result = await self.alerts_collection.insert_one(alert_dict)
            
            logger.info(f"Alert saved for {alert_dict['symbol']}: {alert_dict['condition']}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to save alert: {e}")
            raise
    
    async def get_active_alerts(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get active alerts for symbol or all symbols"""
        try:
            query = {"status": AlertStatus.ACTIVE.value}
            if symbol:
                query["symbol"] = symbol
            
            cursor = self.alerts_collection.find(query)
            alerts = []
            async for doc in cursor:
                doc.pop('_id', None)
                alerts.append(doc)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []
    
    async def update_alert_status(self, alert_id: str, status: AlertStatus, 
                                last_triggered: Optional[datetime] = None):
        """Update alert status and trigger information"""
        try:
            update_data = {"status": status.value}
            if last_triggered:
                update_data["last_triggered"] = last_triggered.isoformat()
                update_data["$inc"] = {"trigger_count": 1}
            
            result = await self.alerts_collection.update_one(
                {"id": alert_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to update alert status: {e}")
            return False
    
    # ==================== BACKTESTING ====================
    
    async def save_backtest_result(self, backtest: BacktestResult) -> str:
        """Save backtesting results"""
        try:
            backtest_dict = backtest.dict() if isinstance(backtest, BacktestResult) else backtest
            result = await self.backtests_collection.insert_one(backtest_dict)
            
            logger.info(f"Backtest saved for {backtest_dict['symbol']}: {backtest_dict['strategy']}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to save backtest: {e}")
            raise
    
    async def get_backtest_results(self, symbol: str = None, 
                                 strategy: str = None) -> List[Dict[str, Any]]:
        """Get historical backtest results"""
        try:
            query = {}
            if symbol:
                query["symbol"] = symbol
            if strategy:
                query["strategy"] = strategy
            
            cursor = self.backtests_collection.find(query).sort("timestamp", -1).limit(10)
            results = []
            async for doc in cursor:
                doc.pop('_id', None)
                results.append(doc)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get backtest results: {e}")
            return []
    
    # ==================== AUDIT LOGGING ====================
    
    async def log_action(self, audit_log: AuditLog):
        """Log action to PostgreSQL audit table"""
        try:
            async with self.postgres_pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO audit_logs 
                    (id, action, symbol, user_id, parameters, result, 
                     execution_time_ms, success, error_message, timestamp)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ''', 
                audit_log.id,
                audit_log.action,
                audit_log.symbol,
                audit_log.user_id,
                json.dumps(audit_log.parameters),
                json.dumps(audit_log.result),
                audit_log.execution_time_ms,
                audit_log.success,
                audit_log.error_message,
                audit_log.timestamp
                )
                
        except Exception as e:
            logger.error(f"Failed to log action: {e}")
            # Don't raise - audit logging shouldn't break main functionality
    
    async def get_audit_logs(self, action: str = None, 
                           start_date: datetime = None,
                           end_date: datetime = None,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit logs with filtering"""
        try:
            query = "SELECT * FROM audit_logs WHERE 1=1"
            params = []
            
            if action:
                query += " AND action = $1"
                params.append(action)
            
            if start_date:
                query += f" AND timestamp >= ${len(params) + 1}"
                params.append(start_date)
            
            if end_date:
                query += f" AND timestamp <= ${len(params) + 1}"
                params.append(end_date)
            
            query += f" ORDER BY timestamp DESC LIMIT ${len(params) + 1}"
            params.append(limit)
            
            async with self.postgres_pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []
    
    # ==================== MARKET CONTEXT CACHING ====================
    
    async def cache_market_context(self, context: MarketContext):
        """Cache market context in Redis"""
        try:
            context_dict = context.dict() if isinstance(context, MarketContext) else context
            await self.redis_client.setex(
                "market_context",
                context.ttl_seconds if hasattr(context, 'ttl_seconds') else self.cache_ttl['market_context'],
                json.dumps(context_dict, default=str)
            )
        except Exception as e:
            logger.error(f"Failed to cache market context: {e}")
    
    async def get_market_context(self) -> Optional[Dict[str, Any]]:
        """Get cached market context"""
        try:
            cached = await self.redis_client.get("market_context")
            return json.loads(cached) if cached else None
        except Exception as e:
            logger.error(f"Failed to get market context: {e}")
            return None
    
    # ==================== UTILITY METHODS ====================
    
    async def health_check(self) -> InfrastructureHealth:
        """Check health of all database connections"""
        health = InfrastructureHealth()
        
        # MongoDB health
        try:
            await self.mongodb_client.admin.command('ping')
            health.mongodb_status = "healthy"
        except Exception as e:
            health.mongodb_status = "error"
            health.errors.append(f"MongoDB: {str(e)}")
        
        # Redis health
        try:
            await self.redis_client.ping()
            health.redis_status = "healthy"
        except Exception as e:
            health.redis_status = "error"
            health.errors.append(f"Redis: {str(e)}")
        
        # PostgreSQL health
        try:
            async with self.postgres_pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
            health.postgres_status = "healthy"
        except Exception as e:
            health.postgres_status = "error"
            health.errors.append(f"PostgreSQL: {str(e)}")
        
        return health
    
    async def cleanup_expired_data(self):
        """Clean up expired alerts, opportunities, and old data"""
        try:
            now = datetime.now(timezone.utc)
            
            # Clean expired alerts
            await self.alerts_collection.update_many(
                {"expires_at": {"$lt": now.isoformat()}},
                {"$set": {"status": AlertStatus.EXPIRED.value}}
            )
            
            # Clean expired opportunities
            await self.opportunities_collection.delete_many({
                "expires_at": {"$lt": now.isoformat()}
            })
            
            # Clean old analysis data (keep 30 days)
            cutoff = now - timedelta(days=30)
            result = await self.analysis_collection.delete_many({
                "timestamp": {"$lt": cutoff.isoformat()}
            })
            
            logger.info(f"Cleanup completed: removed {result.deleted_count} old analysis records")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            metrics = {}
            
            # MongoDB metrics
            mongo_stats = await self.crypto_db.command("dbStats")
            metrics["mongodb"] = {
                "collections": mongo_stats.get("collections", 0),
                "data_size_mb": mongo_stats.get("dataSize", 0) / (1024 * 1024),
                "index_size_mb": mongo_stats.get("indexSize", 0) / (1024 * 1024)
            }
            
            # Redis metrics
            redis_info = await self.redis_client.info()
            metrics["redis"] = {
                "memory_used_mb": redis_info.get("used_memory", 0) / (1024 * 1024),
                "connected_clients": redis_info.get("connected_clients", 0),
                "total_commands": redis_info.get("total_commands_processed", 0)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}