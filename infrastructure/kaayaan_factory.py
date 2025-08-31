"""
Kaayaan Infrastructure Factory
Creates and configures all infrastructure components with Kaayaan production credentials
"""

import asyncio
import logging
from typing import Tuple, Optional
import motor.motor_asyncio as motor
import aioredis
import asyncpg
import aiohttp

from models.kaayaan_models import DatabaseConfig, WhatsAppConfig, InfrastructureHealth
from infrastructure.database_manager import DatabaseManager
from infrastructure.alert_manager import AlertManager
from infrastructure.risk_manager import RiskManager
from infrastructure.market_scanner import MarketScanner
from infrastructure.portfolio_tracker import PortfolioTracker
from infrastructure.backtester import Backtester

logger = logging.getLogger(__name__)

class KaayaanInfrastructureFactory:
    """
    Factory class for creating production-ready infrastructure components
    with Kaayaan database credentials and configurations
    """
    
    # Production Infrastructure Credentials
    INFRASTRUCTURE_CONFIG = {
        "mongodb_uri": "mongodb://username:password@mongodb:27017/",
        "redis_url": "redis://:password@redis:6379",
        "postgres_dsn": "postgresql://user:password@postgresql:5432/database",
        "whatsapp_base_url": "https://your-whatsapp-api.com",
        "whatsapp_session": "your_session_id"
    }
    
    def __init__(self):
        self._mongodb_client: Optional[motor.AsyncIOMotorClient] = None
        self._redis_client: Optional[aioredis.Redis] = None
        self._postgres_pool: Optional[asyncpg.Pool] = None
        self._http_session: Optional[aiohttp.ClientSession] = None
        self._initialized = False
        
    async def initialize(self) -> bool:
        """Initialize all database connections"""
        try:
            logger.info("Initializing Kaayaan infrastructure connections...")
            
            # Initialize MongoDB
            self._mongodb_client = motor.AsyncIOMotorClient(
                self.KAAYAAN_CONFIG["mongodb_uri"],
                maxPoolSize=50,
                minPoolSize=5,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
            
            # Test MongoDB connection
            await self._mongodb_client.admin.command('ping')
            logger.info("✅ MongoDB connection established")
            
            # Initialize Redis
            self._redis_client = aioredis.from_url(
                self.KAAYAAN_CONFIG["redis_url"],
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # Test Redis connection
            await self._redis_client.ping()
            logger.info("✅ Redis connection established")
            
            # Initialize PostgreSQL
            self._postgres_pool = await asyncpg.create_pool(
                self.KAAYAAN_CONFIG["postgres_dsn"],
                min_size=5,
                max_size=20,
                command_timeout=10,
                server_settings={
                    'application_name': 'mcp_crypto_server',
                    'jit': 'off'
                }
            )
            
            # Test PostgreSQL connection
            async with self._postgres_pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
            logger.info("✅ PostgreSQL connection established")
            
            # Initialize HTTP session for WhatsApp API
            self._http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                connector=aiohttp.TCPConnector(limit=100, limit_per_host=20)
            )
            logger.info("✅ HTTP session initialized")
            
            self._initialized = True
            logger.info("🚀 Kaayaan infrastructure fully initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Kaayaan infrastructure: {e}")
            await self._cleanup_partial_connections()
            return False
    
    async def _cleanup_partial_connections(self):
        """Clean up any partial connections on initialization failure"""
        try:
            if self._mongodb_client:
                self._mongodb_client.close()
            if self._redis_client:
                await self._redis_client.close()
            if self._postgres_pool:
                await self._postgres_pool.close()
            if self._http_session:
                await self._http_session.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def create_database_manager(self) -> DatabaseManager:
        """Create configured DatabaseManager"""
        if not self._initialized:
            raise RuntimeError("Infrastructure not initialized. Call initialize() first.")
        
        db_manager = DatabaseManager(
            self._mongodb_client,
            self._redis_client, 
            self._postgres_pool
        )
        
        # Initialize collections and tables
        await db_manager.initialize_collections()
        
        logger.info("✅ DatabaseManager created and initialized")
        return db_manager
    
    async def create_alert_manager(self, database_manager: DatabaseManager) -> AlertManager:
        """Create configured AlertManager"""
        if not self._initialized:
            raise RuntimeError("Infrastructure not initialized. Call initialize() first.")
        
        whatsapp_config = WhatsAppConfig(
            base_url=self.KAAYAAN_CONFIG["whatsapp_base_url"],
            session=self.KAAYAAN_CONFIG["whatsapp_session"],
            timeout_seconds=30
        )
        
        alert_manager = AlertManager(
            database_manager=database_manager,
            http_session=self._http_session,
            whatsapp_config=whatsapp_config
        )
        
        logger.info("✅ AlertManager created")
        return alert_manager
    
    async def create_risk_manager(self, database_manager: DatabaseManager) -> RiskManager:
        """Create configured RiskManager"""
        if not self._initialized:
            raise RuntimeError("Infrastructure not initialized. Call initialize() first.")
        
        risk_manager = RiskManager(database_manager)
        logger.info("✅ RiskManager created")
        return risk_manager
    
    async def create_market_scanner(self, database_manager: DatabaseManager) -> MarketScanner:
        """Create configured MarketScanner"""
        if not self._initialized:
            raise RuntimeError("Infrastructure not initialized. Call initialize() first.")
        
        market_scanner = MarketScanner(database_manager)
        logger.info("✅ MarketScanner created")
        return market_scanner
    
    async def create_portfolio_tracker(self, database_manager: DatabaseManager) -> PortfolioTracker:
        """Create configured PortfolioTracker"""
        if not self._initialized:
            raise RuntimeError("Infrastructure not initialized. Call initialize() first.")
        
        portfolio_tracker = PortfolioTracker(database_manager)
        logger.info("✅ PortfolioTracker created")
        return portfolio_tracker
    
    async def create_backtester(self, database_manager: DatabaseManager) -> Backtester:
        """Create configured Backtester"""
        if not self._initialized:
            raise RuntimeError("Infrastructure not initialized. Call initialize() first.")
        
        backtester = Backtester(database_manager)
        logger.info("✅ Backtester created")
        return backtester
    
    async def create_full_infrastructure(self) -> Tuple[DatabaseManager, AlertManager, RiskManager, 
                                                     MarketScanner, PortfolioTracker, Backtester]:
        """Create all infrastructure components in correct dependency order"""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Creating complete Kaayaan infrastructure...")
        
        # Create database manager first (others depend on it)
        database_manager = await self.create_database_manager()
        
        # Create all other components
        alert_manager = await self.create_alert_manager(database_manager)
        risk_manager = await self.create_risk_manager(database_manager)
        market_scanner = await self.create_market_scanner(database_manager)
        portfolio_tracker = await self.create_portfolio_tracker(database_manager)
        backtester = await self.create_backtester(database_manager)
        
        logger.info("🎉 Complete Kaayaan infrastructure ready for production!")
        
        return (
            database_manager,
            alert_manager,
            risk_manager,
            market_scanner,
            portfolio_tracker,
            backtester
        )
    
    async def health_check(self) -> InfrastructureHealth:
        """Comprehensive health check of all infrastructure components"""
        health = InfrastructureHealth()
        
        if not self._initialized:
            health.errors.append("Infrastructure not initialized")
            return health
        
        # MongoDB health
        try:
            await self._mongodb_client.admin.command('ping')
            health.mongodb_status = "healthy"
        except Exception as e:
            health.mongodb_status = "error"
            health.errors.append(f"MongoDB: {str(e)}")
        
        # Redis health
        try:
            await self._redis_client.ping()
            health.redis_status = "healthy"
        except Exception as e:
            health.redis_status = "error"
            health.errors.append(f"Redis: {str(e)}")
        
        # PostgreSQL health
        try:
            async with self._postgres_pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
            health.postgres_status = "healthy"
        except Exception as e:
            health.postgres_status = "error"
            health.errors.append(f"PostgreSQL: {str(e)}")
        
        # WhatsApp API health
        try:
            async with self._http_session.get(
                f"{self.KAAYAAN_CONFIG['whatsapp_base_url']}/api/sessions",
                timeout=10
            ) as response:
                if response.status == 200:
                    health.whatsapp_status = "healthy"
                else:
                    health.whatsapp_status = "degraded"
                    health.errors.append(f"WhatsApp API returned status {response.status}")
        except Exception as e:
            health.whatsapp_status = "error"
            health.errors.append(f"WhatsApp API: {str(e)}")
        
        return health
    
    async def cleanup(self):
        """Clean up all connections and resources"""
        try:
            logger.info("Cleaning up Kaayaan infrastructure...")
            
            if self._mongodb_client:
                self._mongodb_client.close()
                logger.info("MongoDB connection closed")
            
            if self._redis_client:
                await self._redis_client.close()
                logger.info("Redis connection closed")
            
            if self._postgres_pool:
                await self._postgres_pool.close()
                logger.info("PostgreSQL pool closed")
            
            if self._http_session:
                await self._http_session.close()
                logger.info("HTTP session closed")
            
            self._initialized = False
            logger.info("✅ Kaayaan infrastructure cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    @classmethod
    async def create_for_production(cls) -> 'KaayaanInfrastructureFactory':
        """Class method to create and initialize factory for production use"""
        factory = cls()
        success = await factory.initialize()
        
        if not success:
            await factory.cleanup()
            raise RuntimeError("Failed to initialize Kaayaan infrastructure for production")
        
        return factory
    
    @property
    def is_initialized(self) -> bool:
        """Check if infrastructure is initialized"""
        return self._initialized
    
    @property
    def database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        return DatabaseConfig(
            mongodb_uri=self.KAAYAAN_CONFIG["mongodb_uri"],
            redis_url=self.KAAYAAN_CONFIG["redis_url"],
            postgres_dsn=self.KAAYAAN_CONFIG["postgres_dsn"]
        )
    
    @property
    def whatsapp_config(self) -> WhatsAppConfig:
        """Get WhatsApp configuration"""
        return WhatsAppConfig(
            base_url=self.KAAYAAN_CONFIG["whatsapp_base_url"],
            session=self.KAAYAAN_CONFIG["whatsapp_session"]
        )

# Convenience functions for quick setup
async def create_kaayaan_infrastructure() -> Tuple[DatabaseManager, AlertManager, RiskManager, 
                                                MarketScanner, PortfolioTracker, Backtester]:
    """Convenience function to create complete Kaayaan infrastructure"""
    factory = await KaayaanInfrastructureFactory.create_for_production()
    return await factory.create_full_infrastructure()

async def quick_health_check() -> InfrastructureHealth:
    """Quick health check of Kaayaan infrastructure"""
    try:
        factory = KaayaanInfrastructureFactory()
        await factory.initialize()
        health = await factory.health_check()
        await factory.cleanup()
        return health
    except Exception as e:
        health = InfrastructureHealth()
        health.errors.append(f"Health check failed: {str(e)}")
        return health