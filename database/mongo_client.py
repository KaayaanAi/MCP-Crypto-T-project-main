"""
MongoDB client for Kaayaan infrastructure integration
Handles analysis storage, historical patterns, and portfolio data
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient
import pymongo
import os

logger = logging.getLogger(__name__)

class MongoClient:
    """MongoDB client for cryptocurrency trading data management"""
    
    def __init__(self):
        # Kaayaan infrastructure connection
        self.connection_string = os.getenv(
            "MONGODB_URL", 
            "mongodb://username:password@mongodb:27017/"
        )
        self.database_name = os.getenv("MONGO_DB_NAME", "crypto_trading")
        
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        
    async def connect(self):
        """Establish MongoDB connection"""
        try:
            self.client = AsyncIOMotorClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
            
            # Test connection
            await self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            
            # Create indexes for optimal performance
            await self._create_indexes()
            
            logger.info("MongoDB connection established")
            return True
            
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    async def _create_indexes(self):
        """Create database indexes for performance optimization"""
        try:
            # Analysis collection indexes
            await self.db.analysis.create_index([
                ("symbol", pymongo.ASCENDING),
                ("timestamp", pymongo.DESCENDING)
            ])
            
            await self.db.analysis.create_index([
                ("timeframe", pymongo.ASCENDING),
                ("timestamp", pymongo.DESCENDING)
            ])
            
            # Portfolio collection indexes
            await self.db.portfolios.create_index([
                ("portfolio_id", pymongo.ASCENDING),
                ("updated_at", pymongo.DESCENDING)
            ])
            
            # Opportunities collection indexes
            await self.db.opportunities.create_index([
                ("confidence", pymongo.DESCENDING),
                ("timestamp", pymongo.DESCENDING)
            ])
            
            # Risk assessments indexes
            await self.db.risk_assessments.create_index([
                ("symbol", pymongo.ASCENDING),
                ("timestamp", pymongo.DESCENDING)
            ])
            
            # Alerts collection indexes
            await self.db.alerts.create_index([
                ("symbol", pymongo.ASCENDING),
                ("active", pymongo.ASCENDING)
            ])
            
            # Pattern matching indexes
            await self.db.patterns.create_index([
                ("symbol", pymongo.ASCENDING),
                ("pattern_type", pymongo.ASCENDING),
                ("similarity_score", pymongo.DESCENDING)
            ])
            
            logger.info("MongoDB indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    async def store_analysis(self, analysis_data: Dict[str, Any]) -> bool:
        """Store cryptocurrency analysis with intelligent pattern detection"""
        try:
            # Ensure connection
            if not self.db:
                await self.connect()
            
            # Enrich analysis data
            analysis_data.update({
                "stored_at": datetime.now(timezone.utc),
                "analysis_id": f"{analysis_data['symbol']}_{analysis_data['timestamp']}",
                "market_conditions": await self._extract_market_conditions(analysis_data)
            })
            
            # Store main analysis
            result = await self.db.analysis.insert_one(analysis_data)
            
            # Extract and store patterns for future matching
            await self._extract_and_store_patterns(analysis_data)
            
            logger.info(f"Analysis stored for {analysis_data['symbol']}: {result.inserted_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store analysis: {e}")
            return False
    
    async def store_opportunities(self, opportunities: List[Dict[str, Any]]) -> bool:
        """Store detected trading opportunities"""
        try:
            if not self.db:
                await self.connect()
            
            if not opportunities:
                return True
            
            # Enrich opportunity data
            for opp in opportunities:
                opp.update({
                    "stored_at": datetime.now(timezone.utc),
                    "opportunity_id": f"{opp['symbol']}_{opp['type']}_{opp['timestamp']}",
                    "status": "active"
                })
            
            result = await self.db.opportunities.insert_many(opportunities)
            logger.info(f"Stored {len(opportunities)} opportunities: {len(result.inserted_ids)} inserted")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store opportunities: {e}")
            return False
    
    async def store_risk_assessment(self, risk_data: Dict[str, Any]) -> bool:
        """Store risk assessment with portfolio context"""
        try:
            if not self.db:
                await self.connect()
            
            risk_data.update({
                "stored_at": datetime.now(timezone.utc),
                "risk_id": f"{risk_data['symbol']}_{risk_data['timestamp']}"
            })
            
            result = await self.db.risk_assessments.insert_one(risk_data)
            logger.info(f"Risk assessment stored for {risk_data['symbol']}: {result.inserted_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store risk assessment: {e}")
            return False
    
    async def store_backtest_result(self, backtest_data: Dict[str, Any]) -> bool:
        """Store backtesting results with performance metrics"""
        try:
            if not self.db:
                await self.connect()
            
            backtest_data.update({
                "stored_at": datetime.now(timezone.utc),
                "backtest_id": f"{backtest_data['symbol']}_{backtest_data['strategy_name']}_{backtest_data['start_date']}"
            })
            
            result = await self.db.backtests.insert_one(backtest_data)
            logger.info(f"Backtest result stored: {result.inserted_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store backtest result: {e}")
            return False
    
    async def store_regime_analysis(self, regime_data: Dict[str, Any]) -> bool:
        """Store market regime analysis"""
        try:
            if not self.db:
                await self.connect()
            
            regime_data.update({
                "stored_at": datetime.now(timezone.utc),
                "regime_id": f"regime_{regime_data['timestamp']}"
            })
            
            result = await self.db.market_regimes.insert_one(regime_data)
            logger.info(f"Market regime analysis stored: {result.inserted_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store regime analysis: {e}")
            return False
    
    async def find_similar_patterns(self, symbol: str, current_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find historically similar patterns for intelligent decision making"""
        try:
            if not self.db:
                await self.connect()
            
            # Extract current pattern features
            current_features = self._extract_pattern_features(current_analysis)
            
            # Query for similar patterns using similarity score
            pipeline = [
                {
                    "$match": {
                        "symbol": symbol,
                        "pattern_type": current_features.get("pattern_type"),
                        "volatility_level": current_features.get("volatility_level")
                    }
                },
                {
                    "$addFields": {
                        "similarity_score": {
                            "$subtract": [
                                1,
                                {
                                    "$abs": {
                                        "$subtract": [
                                            "$trend_strength",
                                            current_features.get("trend_strength", 0)
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                },
                {
                    "$match": {
                        "similarity_score": {"$gte": 0.7}
                    }
                },
                {
                    "$sort": {"similarity_score": -1}
                },
                {
                    "$limit": 10
                }
            ]
            
            cursor = self.db.patterns.aggregate(pipeline)
            similar_patterns = await cursor.to_list(length=10)
            
            logger.info(f"Found {len(similar_patterns)} similar patterns for {symbol}")
            return similar_patterns
            
        except Exception as e:
            logger.error(f"Failed to find similar patterns: {e}")
            return []
    
    async def get_portfolio_data(self, portfolio_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve portfolio data with historical performance"""
        try:
            if not self.db:
                await self.connect()
            
            portfolio = await self.db.portfolios.find_one(
                {"portfolio_id": portfolio_id},
                sort=[("updated_at", -1)]
            )
            
            if portfolio:
                # Get historical performance data
                portfolio["historical_performance"] = await self._get_portfolio_history(portfolio_id)
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Failed to get portfolio data: {e}")
            return None
    
    async def update_portfolio(self, portfolio_id: str, updates: Dict[str, Any]) -> bool:
        """Update portfolio with change tracking"""
        try:
            if not self.db:
                await self.connect()
            
            updates.update({
                "updated_at": datetime.now(timezone.utc)
            })
            
            result = await self.db.portfolios.update_one(
                {"portfolio_id": portfolio_id},
                {"$set": updates},
                upsert=True
            )
            
            logger.info(f"Portfolio {portfolio_id} updated: {result.modified_count} documents modified")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update portfolio: {e}")
            return False
    
    async def store_alert(self, alert_data: Dict[str, Any]) -> Optional[str]:
        """Store trading alert with conditions"""
        try:
            if not self.db:
                await self.connect()
            
            alert_data.update({
                "created_at": datetime.now(timezone.utc),
                "active": True,
                "triggered_count": 0
            })
            
            result = await self.db.alerts.insert_one(alert_data)
            alert_id = str(result.inserted_id)
            
            logger.info(f"Alert stored: {alert_id}")
            return alert_id
            
        except Exception as e:
            logger.error(f"Failed to store alert: {e}")
            return None
    
    async def get_active_alerts(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active alerts for monitoring"""
        try:
            if not self.db:
                await self.connect()
            
            query = {"active": True}
            if symbol:
                query["symbol"] = symbol
            
            cursor = self.db.alerts.find(query)
            alerts = await cursor.to_list(length=None)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []
    
    async def update_alert_status(self, alert_id: str, status_updates: Dict[str, Any]) -> bool:
        """Update alert status and trigger count"""
        try:
            if not self.db:
                await self.connect()
            
            from bson import ObjectId
            
            result = await self.db.alerts.update_one(
                {"_id": ObjectId(alert_id)},
                {"$set": status_updates, "$inc": {"triggered_count": 1}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to update alert status: {e}")
            return False
    
    async def get_market_statistics(self, timeframe: str = "24h") -> Dict[str, Any]:
        """Get aggregated market statistics"""
        try:
            if not self.db:
                await self.connect()
            
            # Calculate timeframe for query
            time_cutoff = datetime.now(timezone.utc) - timedelta(
                hours=24 if timeframe == "24h" else 1
            )
            
            pipeline = [
                {
                    "$match": {
                        "timestamp": {"$gte": time_cutoff.isoformat()}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_analyses": {"$sum": 1},
                        "avg_confidence": {"$avg": "$recommendation.confidence"},
                        "buy_signals": {
                            "$sum": {
                                "$cond": [{"$eq": ["$recommendation.action", "BUY"]}, 1, 0]
                            }
                        },
                        "sell_signals": {
                            "$sum": {
                                "$cond": [{"$eq": ["$recommendation.action", "SELL"]}, 1, 0]
                            }
                        },
                        "hold_signals": {
                            "$sum": {
                                "$cond": [{"$eq": ["$recommendation.action", "HOLD"]}, 1, 0]
                            }
                        }
                    }
                }
            ]
            
            cursor = self.db.analysis.aggregate(pipeline)
            stats = await cursor.to_list(length=1)
            
            return stats[0] if stats else {}
            
        except Exception as e:
            logger.error(f"Failed to get market statistics: {e}")
            return {}
    
    async def _extract_market_conditions(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract market conditions for intelligent analysis"""
        return {
            "trend": analysis_data.get("market_analysis", {}).get("trend"),
            "volatility": analysis_data.get("market_analysis", {}).get("volatility"),
            "volume_profile": "high" if analysis_data.get("metadata", {}).get("volume_24h", 0) > 1000000 else "low",
            "institutional_activity": len(analysis_data.get("order_blocks", [])) > 0
        }
    
    async def _extract_and_store_patterns(self, analysis_data: Dict[str, Any]):
        """Extract and store patterns for similarity matching"""
        try:
            pattern_features = self._extract_pattern_features(analysis_data)
            
            pattern_doc = {
                "symbol": analysis_data["symbol"],
                "timestamp": analysis_data["timestamp"],
                "pattern_type": pattern_features["pattern_type"],
                "volatility_level": pattern_features["volatility_level"],
                "trend_strength": pattern_features["trend_strength"],
                "volume_profile": pattern_features["volume_profile"],
                "outcome": None,  # To be updated later with actual performance
                "created_at": datetime.now(timezone.utc)
            }
            
            await self.db.patterns.insert_one(pattern_doc)
            
        except Exception as e:
            logger.error(f"Failed to extract and store patterns: {e}")
    
    def _extract_pattern_features(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract pattern features for similarity matching"""
        market_analysis = analysis_data.get("market_analysis", {})
        
        # Calculate trend strength based on indicators
        trend_strength = 0
        if market_analysis.get("trend") == "bullish":
            trend_strength = market_analysis.get("confidence", 0) / 100
        elif market_analysis.get("trend") == "bearish":
            trend_strength = -(market_analysis.get("confidence", 0) / 100)
        
        # Determine pattern type based on technical indicators
        pattern_type = "consolidation"
        if len(analysis_data.get("break_of_structure", [])) > 0:
            pattern_type = "breakout"
        elif len(analysis_data.get("rsi_divergence", [])) > 0:
            pattern_type = "reversal"
        elif len(analysis_data.get("fair_value_gaps", [])) > 0:
            pattern_type = "gap_fill"
        
        return {
            "pattern_type": pattern_type,
            "volatility_level": market_analysis.get("volatility", "unknown"),
            "trend_strength": trend_strength,
            "volume_profile": analysis_data.get("metadata", {}).get("volume_24h", 0)
        }
    
    async def _get_portfolio_history(self, portfolio_id: str) -> List[Dict[str, Any]]:
        """Get portfolio historical performance data"""
        try:
            cursor = self.db.portfolio_history.find(
                {"portfolio_id": portfolio_id}
            ).sort("timestamp", -1).limit(30)
            
            history = await cursor.to_list(length=30)
            return history
            
        except Exception as e:
            logger.error(f"Failed to get portfolio history: {e}")
            return []

    async def health_check(self) -> Dict[str, Any]:
        """Perform MongoDB health check"""
        try:
            if not self.client:
                await self.connect()
            
            # Test basic operations
            await self.client.admin.command('ping')
            
            # Get database stats
            stats = await self.db.command("dbStats")
            
            return {
                "status": "healthy",
                "database": self.database_name,
                "collections": stats.get("collections", 0),
                "data_size": stats.get("dataSize", 0),
                "index_size": stats.get("indexSize", 0)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }