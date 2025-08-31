"""
Redis client for Kaayaan infrastructure integration
Handles high-performance caching, real-time data, and session management
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
import redis.asyncio as redis
import os

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis client for high-performance caching and real-time data"""
    
    def __init__(self):
        # Kaayaan infrastructure connection
        self.connection_string = os.getenv(
            "REDIS_URL", 
            "redis://:password@redis:6379"
        )
        
        self.client: Optional[redis.Redis] = None
        
        # Cache configuration
        self.default_ttl = int(os.getenv("REDIS_DEFAULT_TTL", 300))  # 5 minutes
        self.analysis_ttl = int(os.getenv("REDIS_ANALYSIS_TTL", 300))  # 5 minutes
        self.market_data_ttl = int(os.getenv("REDIS_MARKET_TTL", 60))  # 1 minute
        
    async def connect(self):
        """Establish Redis connection with connection pooling"""
        try:
            self.client = redis.from_url(
                self.connection_string,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.client.ping()
            
            logger.info("Redis connection established")
            return True
            
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")
    
    # Analysis Caching Methods
    async def cache_analysis(self, cache_key: str, analysis_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache cryptocurrency analysis with intelligent key structure"""
        try:
            if not self.client:
                await self.connect()
            
            ttl = ttl or self.analysis_ttl
            
            # Serialize analysis data
            serialized_data = json.dumps(analysis_data, default=str)
            
            # Store with expiration
            await self.client.setex(
                name=f"analysis:{cache_key}",
                time=ttl,
                value=serialized_data
            )
            
            # Add to analysis index for bulk operations
            await self.client.sadd("analysis_keys", f"analysis:{cache_key}")
            await self.client.expire("analysis_keys", ttl)
            
            logger.debug(f"Analysis cached: {cache_key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache analysis: {e}")
            return False
    
    async def get_analysis(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached analysis with automatic deserialization"""
        try:
            if not self.client:
                await self.connect()
            
            cached_data = await self.client.get(f"analysis:{cache_key}")
            
            if cached_data:
                analysis = json.loads(cached_data)
                logger.debug(f"Analysis cache hit: {cache_key}")
                return analysis
            
            logger.debug(f"Analysis cache miss: {cache_key}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached analysis: {e}")
            return None
    
    # Market Data Caching
    async def cache_market_data(self, symbol: str, market_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache real-time market data with high-frequency updates"""
        try:
            if not self.client:
                await self.connect()
            
            ttl = ttl or self.market_data_ttl
            
            # Store current market data
            await self.client.hset(
                f"market:{symbol}",
                mapping={
                    "price": str(market_data.get("price", 0)),
                    "volume_24h": str(market_data.get("volume_24h", 0)),
                    "change_24h": str(market_data.get("change_24h", 0)),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "market_cap": str(market_data.get("market_cap", 0))
                }
            )
            
            await self.client.expire(f"market:{symbol}", ttl)
            
            # Maintain price history for trend analysis
            await self._update_price_history(symbol, market_data.get("price", 0))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache market data: {e}")
            return False
    
    async def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached market data"""
        try:
            if not self.client:
                await self.connect()
            
            market_data = await self.client.hgetall(f"market:{symbol}")
            
            if market_data:
                # Convert string values back to appropriate types
                return {
                    "price": float(market_data.get("price", 0)),
                    "volume_24h": float(market_data.get("volume_24h", 0)),
                    "change_24h": float(market_data.get("change_24h", 0)),
                    "timestamp": market_data.get("timestamp"),
                    "market_cap": float(market_data.get("market_cap", 0))
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            return None
    
    # Real-time Streaming and Alerts
    async def cache_opportunity(self, opportunity: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Cache trading opportunity with scoring"""
        try:
            if not self.client:
                await self.connect()
            
            ttl = ttl or self.default_ttl
            opportunity_id = f"{opportunity['symbol']}:{opportunity['type']}:{opportunity['timestamp']}"
            
            # Store opportunity
            await self.client.setex(
                f"opportunity:{opportunity_id}",
                ttl,
                json.dumps(opportunity, default=str)
            )
            
            # Add to scored set for ranking
            confidence_score = opportunity.get("confidence", 0)
            await self.client.zadd(
                "opportunities_ranked",
                {f"opportunity:{opportunity_id}": confidence_score}
            )
            await self.client.expire("opportunities_ranked", ttl)
            
            logger.debug(f"Opportunity cached: {opportunity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache opportunity: {e}")
            return False
    
    async def get_top_opportunities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top-ranked trading opportunities"""
        try:
            if not self.client:
                await self.connect()
            
            # Get top opportunities by score (descending)
            opportunity_keys = await self.client.zrevrange(
                "opportunities_ranked", 
                0, 
                limit - 1,
                withscores=True
            )
            
            opportunities = []
            for key, score in opportunity_keys:
                opportunity_data = await self.client.get(key)
                if opportunity_data:
                    opportunity = json.loads(opportunity_data)
                    opportunity["cached_score"] = score
                    opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Failed to get top opportunities: {e}")
            return []
    
    # Session and State Management
    async def store_portfolio_state(self, portfolio_id: str, state: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Store portfolio state for session management"""
        try:
            if not self.client:
                await self.connect()
            
            ttl = ttl or 3600  # 1 hour default for portfolio state
            
            await self.client.setex(
                f"portfolio_state:{portfolio_id}",
                ttl,
                json.dumps(state, default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store portfolio state: {e}")
            return False
    
    async def get_portfolio_state(self, portfolio_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve portfolio state"""
        try:
            if not self.client:
                await self.connect()
            
            state_data = await self.client.get(f"portfolio_state:{portfolio_id}")
            
            if state_data:
                return json.loads(state_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get portfolio state: {e}")
            return None
    
    # Alert and Notification Queuing
    async def queue_alert(self, alert: Dict[str, Any]) -> bool:
        """Queue alert for processing"""
        try:
            if not self.client:
                await self.connect()
            
            alert_data = {
                **alert,
                "queued_at": datetime.now(timezone.utc).isoformat(),
                "status": "pending"
            }
            
            # Add to alert processing queue
            await self.client.lpush(
                "alert_queue",
                json.dumps(alert_data, default=str)
            )
            
            # Set queue expiration to prevent infinite growth
            await self.client.expire("alert_queue", 86400)  # 24 hours
            
            logger.debug(f"Alert queued: {alert.get('alert_type', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue alert: {e}")
            return False
    
    async def process_alert_queue(self, max_alerts: int = 10) -> List[Dict[str, Any]]:
        """Process queued alerts"""
        try:
            if not self.client:
                await self.connect()
            
            alerts = []
            for _ in range(max_alerts):
                alert_data = await self.client.rpop("alert_queue")
                if not alert_data:
                    break
                
                alert = json.loads(alert_data)
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to process alert queue: {e}")
            return []
    
    # Rate Limiting
    async def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> bool:
        """Check if rate limit is exceeded"""
        try:
            if not self.client:
                await self.connect()
            
            current_count = await self.client.incr(f"rate_limit:{key}")
            
            if current_count == 1:
                await self.client.expire(f"rate_limit:{key}", window_seconds)
            
            return current_count <= limit
            
        except Exception as e:
            logger.error(f"Failed to check rate limit: {e}")
            return True  # Allow on error to prevent blocking
    
    async def get_rate_limit_status(self, key: str) -> Dict[str, Any]:
        """Get current rate limit status"""
        try:
            if not self.client:
                await self.connect()
            
            current_count = await self.client.get(f"rate_limit:{key}")
            ttl = await self.client.ttl(f"rate_limit:{key}")
            
            return {
                "current_count": int(current_count) if current_count else 0,
                "remaining_time": ttl if ttl > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
            return {"current_count": 0, "remaining_time": 0}
    
    # Market Scanning Cache
    async def cache_scan_results(self, scan_type: str, results: List[Dict[str, Any]], ttl: Optional[int] = None) -> bool:
        """Cache market scan results"""
        try:
            if not self.client:
                await self.connect()
            
            ttl = ttl or 180  # 3 minutes for scan results
            
            await self.client.setex(
                f"scan:{scan_type}:{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}",
                ttl,
                json.dumps(results, default=str)
            )
            
            # Keep latest scan results easily accessible
            await self.client.setex(
                f"scan:latest:{scan_type}",
                ttl,
                json.dumps(results, default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache scan results: {e}")
            return False
    
    async def get_latest_scan_results(self, scan_type: str) -> Optional[List[Dict[str, Any]]]:
        """Get latest scan results"""
        try:
            if not self.client:
                await self.connect()
            
            results_data = await self.client.get(f"scan:latest:{scan_type}")
            
            if results_data:
                return json.loads(results_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get scan results: {e}")
            return None
    
    # Performance Metrics
    async def track_performance_metric(self, metric_name: str, value: float, timestamp: Optional[datetime] = None):
        """Track performance metrics in time series"""
        try:
            if not self.client:
                await self.connect()
            
            timestamp = timestamp or datetime.now(timezone.utc)
            score = timestamp.timestamp()
            
            # Store in sorted set with timestamp as score
            await self.client.zadd(
                f"metrics:{metric_name}",
                {f"{value}:{timestamp.isoformat()}": score}
            )
            
            # Keep only last 24 hours of data
            cutoff_time = (datetime.now(timezone.utc) - timedelta(days=1)).timestamp()
            await self.client.zremrangebyscore(f"metrics:{metric_name}", 0, cutoff_time)
            
        except Exception as e:
            logger.error(f"Failed to track performance metric: {e}")
    
    async def get_performance_metrics(self, metric_name: str, hours_back: int = 24) -> List[Dict[str, Any]]:
        """Get performance metrics for specified time range"""
        try:
            if not self.client:
                await self.connect()
            
            cutoff_time = (datetime.now(timezone.utc) - timedelta(hours=hours_back)).timestamp()
            
            metrics_data = await self.client.zrangebyscore(
                f"metrics:{metric_name}",
                cutoff_time,
                "+inf",
                withscores=True
            )
            
            metrics = []
            for data, score in metrics_data:
                value_str, timestamp_str = data.split(":", 1)
                metrics.append({
                    "value": float(value_str),
                    "timestamp": timestamp_str,
                    "score": score
                })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return []
    
    # Utility Methods
    async def _update_price_history(self, symbol: str, price: float):
        """Maintain price history for trend analysis"""
        try:
            timestamp = datetime.now(timezone.utc).timestamp()
            
            # Add to price history (limited to last 100 points)
            await self.client.zadd(
                f"price_history:{symbol}",
                {str(price): timestamp}
            )
            
            # Keep only recent prices
            await self.client.zremrangebyrank(f"price_history:{symbol}", 0, -101)
            
        except Exception as e:
            logger.error(f"Failed to update price history: {e}")
    
    async def get_price_history(self, symbol: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent price history"""
        try:
            if not self.client:
                await self.connect()
            
            price_data = await self.client.zrevrange(
                f"price_history:{symbol}",
                0,
                limit - 1,
                withscores=True
            )
            
            history = []
            for price_str, timestamp in price_data:
                history.append({
                    "price": float(price_str),
                    "timestamp": datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get price history: {e}")
            return []
    
    async def clear_cache_pattern(self, pattern: str) -> int:
        """Clear cache entries matching pattern"""
        try:
            if not self.client:
                await self.connect()
            
            keys = await self.client.keys(pattern)
            if keys:
                deleted = await self.client.delete(*keys)
                logger.info(f"Cleared {deleted} cache entries matching pattern: {pattern}")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to clear cache pattern: {e}")
            return 0
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform Redis health check"""
        try:
            if not self.client:
                await self.connect()
            
            # Test basic operations
            await self.client.ping()
            
            # Get Redis info
            info = await self.client.info()
            
            return {
                "status": "healthy",
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory_human"),
                "total_commands_processed": info.get("total_commands_processed")
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }