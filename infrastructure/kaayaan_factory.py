"""
Kaayaan Infrastructure Factory
Creates and configures all infrastructure components with Kaayaan production credentials
"""

import asyncio
import logging
from typing import Tuple
import motor.motor_asyncio as motor
import redis.asyncio as redis
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
    
    # Production Infrastructure Credentials - Now using environment variables
    @property
    def INFRASTRUCTURE_CONFIG(self):
        """Get infrastructure configuration from environment variables"""
        import os

        # Generate secure default values for development if not set
        def get_secure_default(key: str, default_pattern: str) -> str:
            env_value = os.getenv(key)
            if env_value and not env_value.startswith('REPLACE_WITH_'):
                return env_value
            return default_pattern

        return {
            "mongodb_uri": get_secure_default(
                "MONGODB_URI",
                f"mongodb://{os.getenv('MONGO_INITDB_ROOT_USERNAME', 'mcp_crypto_admin')}:{os.getenv('MONGO_INITDB_ROOT_PASSWORD', 'dev_password_change_me')}@mongodb:27017/{os.getenv('MONGO_INITDB_DATABASE', 'crypto_trading')}"
            ),
            "redis_url": get_secure_default(
                "REDIS_URL",
                f"redis://:{os.getenv('REDIS_PASSWORD', 'dev_password_change_me')}@redis:6379"
            ),
            "postgres_dsn": get_secure_default(
                "POSTGRES_DSN",
                f"postgresql://{os.getenv('POSTGRES_USER', 'mcp_crypto_user')}:{os.getenv('POSTGRES_PASSWORD', 'dev_password_change_me')}@postgresql:5432/{os.getenv('POSTGRES_DB', 'crypto_trading')}"
            ),
            "whatsapp_base_url": os.getenv("WHATSAPP_API", "https://api.whatsapp.business.com"),
            "whatsapp_session": os.getenv("WHATSAPP_SESSION", "development_session_id")
        }
    
    def __init__(self):
        self._mongodb_client: motor.AsyncIOMotorClient | None = None
        self._redis_client: redis.Redis | None = None
        self._postgres_pool: asyncpg.Pool | None = None
        self._http_session: aiohttp.ClientSession | None = None
        self._initialized = False
        
    async def initialize(self) -> bool:
        """Initialize all database connections with retry logic and graceful degradation"""
        try:
            logger.info("Initializing Kaayaan infrastructure connections...")

            # Initialize MongoDB with retry logic
            try:
                self._mongodb_client = motor.AsyncIOMotorClient(
                    self.INFRASTRUCTURE_CONFIG["mongodb_uri"],
                    maxPoolSize=50,
                    minPoolSize=5,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000
                )

                # Test MongoDB connection with retry
                for attempt in range(3):
                    try:
                        await self._mongodb_client.admin.command('ping')
                        logger.info("✅ MongoDB connection established")
                        break
                    except Exception as e:
                        if attempt == 2:
                            logger.warning(f"⚠️ MongoDB connection failed after 3 attempts: {e}")
                            self._mongodb_client = None
                        else:
                            logger.info(f"MongoDB connection attempt {attempt + 1} failed, retrying...")
                            await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"⚠️ MongoDB initialization failed: {e}")
                self._mongodb_client = None

            # Initialize Redis with retry logic
            try:
                self._redis_client = redis.from_url(
                    self.INFRASTRUCTURE_CONFIG["redis_url"],
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=20,
                    retry_on_timeout=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )

                # Test Redis connection with retry
                for attempt in range(3):
                    try:
                        await self._redis_client.ping()
                        logger.info("✅ Redis connection established")
                        break
                    except Exception as e:
                        if attempt == 2:
                            logger.warning(f"⚠️ Redis connection failed after 3 attempts: {e}")
                            self._redis_client = None
                        else:
                            logger.info(f"Redis connection attempt {attempt + 1} failed, retrying...")
                            await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"⚠️ Redis initialization failed: {e}")
                self._redis_client = None
            
            # Initialize PostgreSQL with retry logic
            try:
                for attempt in range(3):
                    try:
                        self._postgres_pool = await asyncpg.create_pool(
                            self.INFRASTRUCTURE_CONFIG["postgres_dsn"],
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
                        break
                    except Exception as e:
                        if self._postgres_pool:
                            await self._postgres_pool.close()
                            self._postgres_pool = None
                        if attempt == 2:
                            logger.warning(f"⚠️ PostgreSQL connection failed after 3 attempts: {e}")
                        else:
                            logger.info(f"PostgreSQL connection attempt {attempt + 1} failed, retrying...")
                            await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"⚠️ PostgreSQL initialization failed: {e}")
                self._postgres_pool = None
            
            # Initialize HTTP session for WhatsApp API
            try:
                self._http_session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30),
                    connector=aiohttp.TCPConnector(limit=100, limit_per_host=20)
                )
                logger.info("✅ HTTP session initialized")
            except Exception as e:
                logger.warning(f"⚠️ HTTP session initialization failed: {e}")
                self._http_session = None

            # Check if at least one core service is available
            available_services = []
            if self._mongodb_client:
                available_services.append("MongoDB")
            if self._redis_client:
                available_services.append("Redis")
            if self._postgres_pool:
                available_services.append("PostgreSQL")
            if self._http_session:
                available_services.append("HTTP")

            if available_services:
                self._initialized = True
                logger.info(f"🚀 Kaayaan infrastructure partially initialized with: {', '.join(available_services)}")
                if len(available_services) < 4:
                    logger.warning("⚠️ Some services failed to initialize - running in degraded mode")
                return True
            else:
                logger.error("❌ No infrastructure services could be initialized")
                await self._cleanup_partial_connections()
                return False

        except Exception as e:
            logger.error(f"❌ Critical error during Kaayaan infrastructure initialization: {e}")
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
        """Create configured DatabaseManager with graceful degradation"""
        if not self._initialized:
            raise RuntimeError("Infrastructure not initialized. Call initialize() first.")

        # Log which services are available
        available_services = []
        if self._mongodb_client:
            available_services.append("MongoDB")
        if self._redis_client:
            available_services.append("Redis")
        if self._postgres_pool:
            available_services.append("PostgreSQL")

        if not available_services:
            raise RuntimeError("No database services available")

        logger.info(f"Creating DatabaseManager with: {', '.join(available_services)}")

        db_manager = DatabaseManager(
            self._mongodb_client,
            self._redis_client,
            self._postgres_pool
        )

        # Initialize collections and tables (with error handling)
        try:
            await db_manager.initialize_collections()
            logger.info("✅ DatabaseManager created and initialized")
        except Exception as e:
            logger.warning(f"⚠️ Database initialization had issues: {e}")
            logger.info("✅ DatabaseManager created in degraded mode")

        return db_manager
    
    async def create_alert_manager(self, database_manager: DatabaseManager) -> AlertManager:
        """Create configured AlertManager with graceful degradation"""
        if not self._initialized:
            raise RuntimeError("Infrastructure not initialized. Call initialize() first.")

        whatsapp_config = WhatsAppConfig(
            base_url=self.INFRASTRUCTURE_CONFIG["whatsapp_base_url"],
            session=self.INFRASTRUCTURE_CONFIG["whatsapp_session"],
            timeout_seconds=30
        )

        if not self._http_session:
            logger.warning("⚠️ HTTP session not available - AlertManager will have limited functionality")

        alert_manager = AlertManager(
            database_manager=database_manager,
            http_session=self._http_session,
            whatsapp_config=whatsapp_config
        )

        status = "with WhatsApp integration" if self._http_session else "in limited mode (no WhatsApp)"
        logger.info(f"✅ AlertManager created {status}")
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
    
    async def create_full_infrastructure(self) -> tuple[DatabaseManager, AlertManager, RiskManager, 
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
                f"{self.INFRASTRUCTURE_CONFIG['whatsapp_base_url']}/api/sessions",
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
            mongodb_uri=self.INFRASTRUCTURE_CONFIG["mongodb_uri"],
            redis_url=self.INFRASTRUCTURE_CONFIG["redis_url"],
            postgres_dsn=self.INFRASTRUCTURE_CONFIG["postgres_dsn"]
        )
    
    @property
    def whatsapp_config(self) -> WhatsAppConfig:
        """Get WhatsApp configuration"""
        return WhatsAppConfig(
            base_url=self.INFRASTRUCTURE_CONFIG["whatsapp_base_url"],
            session=self.INFRASTRUCTURE_CONFIG["whatsapp_session"]
        )

# Convenience functions for quick setup
async def create_kaayaan_infrastructure() -> tuple[DatabaseManager, AlertManager, RiskManager, 
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